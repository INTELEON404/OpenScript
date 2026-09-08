#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import time

try:
    from googlesearch import search
except ImportError:
    print("\033[91m[!] Missing dependency: googlesearch-python\033[0m")
    print("\033[93m[*] Install it using: pip install googlesearch-python\033[0m")
    sys.exit(1)


class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


def save_results(results: list, filename: str) -> None:
    """Saves fetched search results to a file."""
    try:
        if not filename.endswith(".txt"):
            filename += ".txt"
        with open(filename, "w", encoding="utf-8") as file:
            for line in results:
                file.write(f"{line}\n")
        print(f"\n{Colors.GREEN}[+] Results successfully saved to: {filename}{Colors.RESET}")
    except IOError as e:
        print(f"{Colors.RED}[!] Error writing to file: {e}{Colors.RESET}")


def perform_search(query: str, max_results: float, delay: int = 2) -> list:
    """Fetches search results from Google."""
    print(f"\n{Colors.BLUE}[*] Query: {query}{Colors.RESET}")
    print(f"{Colors.BLUE}[*] Fetching results... (Delay: {delay}s per batch){Colors.RESET}\n")

    results = []
    try:
        for url in search(query, sleep_interval=delay):
            print(f"{Colors.YELLOW}[+]{Colors.RESET} {url}")
            results.append(url)
            
            if len(results) >= max_results:
                break
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Search interrupted by user.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}[!] Search error (possible rate limit): {e}{Colors.RESET}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Google Search & Utility Script")
    parser.add_argument("-q", "--query", type=str, help="Search query")
    parser.add_argument("-n", "--num", type=str, help="Number of results (or 'all')", default="10")
    parser.add_argument("-o", "--output", type=str, help="Output filename to save results")
    parser.add_argument("-d", "--delay", type=int, help="Delay between requests in seconds", default=2)

    args = parser.parse_args()

    query = args.query
    output = args.output
    delay = args.delay

    # Parse max_results
    if args.num.lower() == "all":
        max_results = float("inf")
    else:
        try:
            max_results = int(args.num)
        except ValueError:
            max_results = 10

    if not query:
        try:
            query = input(f"{Colors.BLUE}[+] Enter Search Query: {Colors.RESET}").strip()
            if not query:
                print(f"{Colors.RED}[!] Query cannot be empty.{Colors.RESET}")
                sys.exit(1)

            choice = input(f"{Colors.BLUE}[+] Total results to fetch (default 10, 'all' for max): {Colors.RESET}").strip().lower()
            if choice == "all":
                max_results = float("inf")
            elif choice.isdigit():
                max_results = int(choice)

            save_opt = input(f"{Colors.BLUE}[+] Save output to file? (y/N): {Colors.RESET}").strip().lower()
            if save_opt == "y":
                output = input(f"{Colors.BLUE}[+] Enter filename (default: dorks_output.txt): {Colors.RESET}").strip() or "dorks_output.txt"
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}[!] Exiting...{Colors.RESET}")
            sys.exit(0)

    results = perform_search(query, max_results, delay)

    if output and results:
        save_results(results, output)

    print(f"{Colors.GREEN}\n[✔] Operation complete. Total URLs fetched: {len(results)}{Colors.RESET}")


if __name__ == "__main__":
    main()
