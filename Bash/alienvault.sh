#!/usr/bin/env bash

BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[*]${NC} $1" >&2; }
success() { echo -e "${GREEN}[+]${NC} $1" >&2; }
error() { echo -e "${RED}[!]${NC} $1" >&2; exit 1; }

command -v jq &>/dev/null || error "'jq' is required but not installed."

DOMAIN="${1:-}"
[[ -z "$DOMAIN" ]] && error "Usage: $0 <domain>"

PAGE=1
LIMIT=500

log "Fetching AlienVault OTX URLs for: ${DOMAIN}"

while true; do
  log "Fetching page ${PAGE}..."

  RESPONSE=$(curl -s "https://otx.alienvault.com/api/v1/indicators/hostname/${DOMAIN}/url_list?limit=${LIMIT}&page=${PAGE}")
  
  URLS=$(echo "$RESPONSE" | jq -r '.url_list[]?.url // empty')
  COUNT=$(echo "$RESPONSE" | jq -r '(.url_list | length) // 0')

  if [[ -z "$URLS" || "$COUNT" -eq 0 ]]; then
    log "No URLs found on page ${PAGE}."
    break
  fi

  echo "$URLS"

  success "Found ${COUNT} URL(s) on page ${PAGE}."

  if (( COUNT < LIMIT )); then
    log "Reached the last page."
    break
  fi

  PAGE=$((PAGE + 1))
done

success "Completed fetching URLs."
