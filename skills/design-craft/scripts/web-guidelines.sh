#!/usr/bin/env bash
# web-guidelines.sh — print the current Vercel Web Interface Guidelines (the rules used for
# the accessibility / consistency half of a design review).
#
#   web-guidelines.sh            # print rules (refetches when older than 24h)
#   web-guidelines.sh --force    # force a refetch
#   web-guidelines.sh --path     # just print the local cache path
#
# The rules live remotely so this skill does not freeze yesterday's checklist. If the network
# is down, the last cached copy is printed instead of failing.

set -euo pipefail

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/design-craft"
CACHE="$CACHE_DIR/web-interface-guidelines.md"
SRC="https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md"
MAX_AGE=$((24 * 3600))

FORCE=0
PATH_ONLY=0
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    --path)  PATH_ONLY=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "web-guidelines.sh: unknown flag: $a" >&2; exit 2 ;;
  esac
done

[ "$PATH_ONLY" = 1 ] && { echo "$CACHE"; exit 0; }

mkdir -p "$CACHE_DIR"
fresh() { [ -s "$CACHE" ] && [ "$FORCE" = 0 ] && [ $(( $(date +%s) - $(stat -c %Y "$CACHE") )) -lt $MAX_AGE ]; }

if ! fresh; then
  if curl -sfL --max-time 25 "$SRC" -o "$CACHE.tmp"; then
    mv "$CACHE.tmp" "$CACHE"
  else
    rm -f "$CACHE.tmp"
    echo "web-guidelines.sh: fetch failed; using cached copy from $(date -r "$CACHE" '+%F %T' 2>/dev/null || echo 'never')" >&2
    [ -s "$CACHE" ] || { echo "web-guidelines.sh: no cache available — check network" >&2; exit 1; }
  fi
fi

cat "$CACHE"
