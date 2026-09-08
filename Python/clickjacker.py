import asyncio
import httpx
import pandas as pd
import argparse
import webbrowser
from datetime import datetime


class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def normalize_url(url):
    url = url.strip()
    if not url.startswith("http"):
        return "https://" + url
    return url


# ── CSP frame-ancestors parsing ─────────────────────────
def parse_frame_ancestors(csp_header):
    """
    Isolate the frame-ancestors directive's own value from the full CSP
    header instead of substring-matching the whole header. A raw
    substring check (`"*" in csp`) can match tokens from a totally
    different directive (e.g. `script-src *`) and misclassify a page as
    protected when frame-ancestors was never actually restricted, or
    vice versa. Returns None if no frame-ancestors directive is present,
    otherwise the list of source tokens (lowercased).
    """
    if not csp_header:
        return None
    for directive in csp_header.split(";"):
        directive = directive.strip()
        if directive.lower().startswith("frame-ancestors"):
            parts = directive.split()
            return [p.strip().lower() for p in parts[1:]]  # tokens after the directive name
    return None


def evaluate_clickjacking(headers):
    """
    Returns (vulnerable: bool, reason: str, evidence: str).

    Precedence matches real browser behavior: when a CSP frame-ancestors
    directive is present, browsers that support CSP honor it and IGNORE
    X-Frame-Options entirely. So frame-ancestors is checked first and,
    if present, is authoritative — XFO is only consulted as a fallback
    when no frame-ancestors directive exists.
    """
    xfo = headers.get("x-frame-options", "").strip()
    csp = headers.get("content-security-policy", "").strip()

    fa_tokens = parse_frame_ancestors(csp)

    if fa_tokens is not None:
        if "'none'" in fa_tokens or "none" in fa_tokens:
            return False, "Protected (CSP)", f"frame-ancestors {' '.join(fa_tokens)}"
        if "*" in fa_tokens:
            return True, "Vulnerable (CSP allows any origin)", f"frame-ancestors {' '.join(fa_tokens)}"
        if fa_tokens == ["'self'"]:
            return False, "Protected (CSP, same-origin only)", f"frame-ancestors {' '.join(fa_tokens)}"
        if fa_tokens:
            # Restricted to specific named origin(s) — not wildcard, not none.
            return False, "Protected (CSP, restricted origins)", f"frame-ancestors {' '.join(fa_tokens)}"
        # frame-ancestors present but empty — treat as no restriction (misconfigured)
        return True, "Vulnerable (empty frame-ancestors)", "frame-ancestors (empty value)"

    # No CSP frame-ancestors — fall back to X-Frame-Options
    if xfo:
        xfo_l = xfo.lower()
        if "deny" in xfo_l or "sameorigin" in xfo_l:
            return False, "Protected (X-Frame-Options)", f"X-Frame-Options: {xfo}"
        # ALLOW-FROM is deprecated and ignored by modern browsers — offers no real protection
        return True, "Vulnerable (X-Frame-Options: ALLOW-FROM is deprecated/ignored by modern browsers)", f"X-Frame-Options: {xfo}"

    return True, "Vulnerable (no X-Frame-Options or CSP frame-ancestors header)", "No relevant headers found"


# ── Scan logic ───────────────────────────────────────────
async def scan_target(url, client, timeout, semaphore):
    url = normalize_url(url)
    async with semaphore:
        try:
            res = await client.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
            headers = {k.lower(): v for k, v in res.headers.items()}
            vulnerable, reason, evidence = evaluate_clickjacking(headers)

            return {
                "url": url,
                "final_url": str(res.url),
                "status_code": res.status_code,
                "status": "Vulnerable" if vulnerable else "Not Vulnerable",
                "reason": reason,
                "evidence": evidence,
            }

        except httpx.TimeoutException:
            return {"url": url, "final_url": url, "status_code": None,
                     "status": "Error", "reason": "Request timed out", "evidence": ""}
        except httpx.ConnectError:
            return {"url": url, "final_url": url, "status_code": None,
                     "status": "Error", "reason": "Connection failed", "evidence": ""}
        except Exception as e:
            return {"url": url, "final_url": url, "status_code": None,
                     "status": "Error", "reason": str(e), "evidence": ""}


# ── Load targets ─────────────────────────────────────────
def load_targets(file_path):
    if file_path.endswith(".txt"):
        with open(file_path) as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        urls = df.iloc[:, 0].dropna().astype(str).tolist()

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
        urls = df.iloc[:, 0].dropna().astype(str).tolist()

    else:
        raise Exception("Unsupported file format (use .txt, .csv, or .xlsx)")

    # de-dupe while preserving order
    seen = set()
    ordered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


# ── Async scan with bounded concurrency + progress ────────
async def run_scan(urls, concurrency=20, timeout=8.0):
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    done = 0
    total = len(urls)

    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(scan_target(u, client, timeout, semaphore)) for u in urls]
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            done += 1
            if total > 1 and (done % 10 == 0 or done == total):
                print(f"[i] Progress: {done}/{total}", end="\r" if done != total else "\n")

    # keep output order matching input order
    order = {u: i for i, u in enumerate(urls)}
    results.sort(key=lambda r: order.get(r["url"], 0))
    return results


# ── Terminal output ───────────────────────────────────────
def print_results(results, open_vuln=False):
    vuln_count = sum(1 for r in results if r["status"] == "Vulnerable")
    safe_count = sum(1 for r in results if r["status"] == "Not Vulnerable")
    error_count = sum(1 for r in results if r["status"] == "Error")

    for r in results:
        if r["status"] == "Vulnerable":
            print(f"{C.RED}{C.BOLD}[ VULNERABLE ]{C.RESET}  {r['url']}  {C.DIM}- {r['reason']}{C.RESET}")
            if open_vuln:
                webbrowser.open(r["url"])
        elif r["status"] == "Not Vulnerable":
            print(f"{C.GREEN}{C.BOLD}[ SAFE       ]{C.RESET}  {r['url']}  {C.DIM}- {r['reason']}{C.RESET}")
        else:
            print(f"{C.YELLOW}{C.BOLD}[ ERROR      ]{C.RESET}  {r['url']}  {C.DIM}- {r['reason']}{C.RESET}")

    print()
    print(f"Summary: {C.RED}{vuln_count} vulnerable{C.RESET}, {C.GREEN}{safe_count} safe{C.RESET}, {C.YELLOW}{error_count} error(s){C.RESET}  (of {len(results)} total)")


# ── TXT report ─────────────────────────────────────────────
def generate_txt(results, filename):
    vuln_count = sum(1 for r in results if r["status"] == "Vulnerable")
    safe_count = sum(1 for r in results if r["status"] == "Not Vulnerable")
    error_count = sum(1 for r in results if r["status"] == "Error")

    lines = []
    lines.append("Clickjacking Scan Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append(f"Vulnerable : {vuln_count}")
    lines.append(f"Safe       : {safe_count}")
    lines.append(f"Errors     : {error_count}")
    lines.append(f"Total      : {len(results)}")
    lines.append("")

    for r in results:
        lines.append("-" * 60)
        lines.append(f"URL       : {r['url']}")
        if r["final_url"] != r["url"]:
            lines.append(f"Final URL : {r['final_url']}  (redirected)")
        if r["status_code"] is not None:
            lines.append(f"Status    : {r['status_code']}")
        lines.append(f"Result    : {r['status']}")
        lines.append(f"Reason    : {r['reason']}")
        if r["evidence"]:
            lines.append(f"Evidence  : {r['evidence']}")
        lines.append("")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Report saved: {filename}")


# ── HTML report ────────────────────────────────────────────
def generate_html(results, filename):
    vuln_count = sum(1 for r in results if r["status"] == "Vulnerable")
    safe_count = sum(1 for r in results if r["status"] == "Not Vulnerable")
    error_count = sum(1 for r in results if r["status"] == "Error")

    rows = []
    for r in results:
        if r["status"] == "Vulnerable":
            status_html = '<span class="vuln">Vulnerable</span>'
        elif r["status"] == "Not Vulnerable":
            status_html = '<span class="safe">Safe</span>'
        else:
            status_html = '<span class="error">Error</span>'

        url_html = f'<a href="{r["url"]}" target="_blank">{r["url"]}</a>'
        code_html = r["status_code"] if r["status_code"] is not None else "-"

        rows.append(f"""
        <tr>
            <td>{url_html}</td>
            <td>{code_html}</td>
            <td>{status_html}</td>
            <td>{r['reason']}</td>
            <td class="evidence">{r['evidence']}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Clickjacking Report</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: white; padding: 20px; }}
    h2 {{ text-align: center; }}
    .summary {{ text-align: center; margin-bottom: 1.5rem; color: #94a3b8; }}
    .summary span {{ margin: 0 1rem; }}
    table {{ width: 90%; margin: 20px auto; border-collapse: collapse; }}
    th, td {{ border: 1px solid #334155; padding: 10px; text-align: left; font-size: 0.9rem; }}
    th {{ background: #1e293b; }}
    .vuln  {{ color: #f87171; font-weight: bold; }}
    .safe  {{ color: #4ade80; font-weight: bold; }}
    .error {{ color: #fbbf24; font-weight: bold; }}
    .evidence {{ color: #94a3b8; font-family: monospace; font-size: 0.8rem; }}
    a {{ color: #38bdf8; text-decoration: none; }}
</style>
</head>
<body>

<h2>Clickjacking Scan Report</h2>
<div class="summary">
    <span><strong>Vulnerable:</strong> {vuln_count}</span>
    <span><strong>Safe:</strong> {safe_count}</span>
    <span><strong>Errors:</strong> {error_count}</span>
    <span><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
</div>

<table>
    <tr>
        <th>Target URL</th>
        <th>HTTP Status</th>
        <th>Result</th>
        <th>Reason</th>
        <th>Evidence</th>
    </tr>
    {"".join(rows)}
</table>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Report saved: {filename}")


def save_report(results, filename):
    if filename.lower().endswith(".html"):
        generate_html(results, filename)
    else:
        generate_txt(results, filename)


# ── Main ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Clickjacking Scanner CLI")

    parser.add_argument("-u", "--url", help="Single URL")
    parser.add_argument("-f", "--file", help="File with URLs (.txt, .csv, .xlsx)")
    parser.add_argument("-o", "--output", help="Save report (.txt or .html, based on extension)")
    parser.add_argument("--open", action="store_true", help="Open vulnerable sites in browser")
    parser.add_argument("--concurrency", type=int, default=20, metavar="N",
                        help="Max concurrent requests (default: 20)")
    parser.add_argument("--timeout", type=float, default=8.0, metavar="S",
                        help="Request timeout in seconds (default: 8.0)")

    args = parser.parse_args()

    if not args.url and not args.file:
        print("[-] Provide --url or --file")
        return

    if args.url:
        urls = [args.url]
    else:
        urls = load_targets(args.file)

    if not urls:
        print("[-] No URLs found to scan")
        return

    print(f"[i] Scanning {len(urls)} target(s) (concurrency={args.concurrency}, timeout={args.timeout}s)")
    results = asyncio.run(run_scan(urls, concurrency=args.concurrency, timeout=args.timeout))

    print_results(results, args.open)

    if args.output:
        save_report(results, args.output)


if __name__ == "__main__":
    main()
