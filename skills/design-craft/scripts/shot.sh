#!/usr/bin/env bash
# shot.sh — headless screenshot of a URL or a local HTML file, for the design review loop.
#
#   shot.sh <url|file> <out.png> [--width 1440] [--height 900] [--full] [--device <name>]
#           [--session <name>] [--wait <ms>] [--dark]
#
# Runs invisibly: uses the Linux agent-browser (playwright chromium) with a throwaway session,
# so nothing pops up on screen. Falls back to Chrome CDP only when the page needs a login.
#
# Examples
#   shot.sh http://localhost:5173 /tmp/opencode/home.png --width 1440 --full
#   shot.sh ./deck.html /tmp/opencode/slide-1.png --width 1920 --height 1080
#   shot.sh https://example.com /tmp/opencode/x.png --width 375 --height 812
#
# Prints the absolute PNG path on success. Exit 1 with a clear message on failure.

set -euo pipefail

BIN="${AGENT_BROWSER_BIN:-$HOME/.local/bin/agent-browser-local}"
URL=""
OUT=""
WIDTH=1440
HEIGHT=900
FULL=0
DEVICE=""
SESSION=""
WAIT=900
DARK=0

die() { echo "shot.sh: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --width)   WIDTH="$2"; shift 2 ;;
    --height)  HEIGHT="$2"; shift 2 ;;
    --full)    FULL=1; shift ;;
    --device)  DEVICE="$2"; shift 2 ;;
    --session) SESSION="$2"; shift 2 ;;
    --wait)    WAIT="$2"; shift 2 ;;
    --dark)    DARK=1; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *) if [ -z "$URL" ]; then URL="$1"; elif [ -z "$OUT" ]; then OUT="$1";
       else die "unexpected argument: $1"; fi; shift ;;
  esac
done

[ -n "$URL" ] || die "usage: shot.sh <url|file> <out.png> [--width N] [--full]"
[ -n "$OUT" ] || OUT="/tmp/opencode/shot-$(date +%s).png"
[ -x "$BIN" ] || die "agent-browser not found at $BIN (set AGENT_BROWSER_BIN)"

# local file -> file:// URL, resolved absolute
case "$URL" in
  http://*|https://*|file://*) : ;;
  *) [ -f "$URL" ] || die "no such file: $URL"
     URL="file://$(realpath "$URL")" ;;
esac

mkdir -p "$(dirname "$OUT")"
OUT="$(realpath -m "$OUT")"
[ -n "$SESSION" ] || SESSION="shot-$$"

cleanup() { "$BIN" --session "$SESSION" close >/dev/null 2>&1 || true; }
trap cleanup EXIT

ARGS=(--session "$SESSION")
# viewport / device are `set` subcommands in agent-browser, not top-level commands.
if [ -n "$DEVICE" ]; then
  "$BIN" "${ARGS[@]}" set device "$DEVICE" >/dev/null 2>&1 || die "unknown device: $DEVICE"
else
  "$BIN" "${ARGS[@]}" set viewport "$WIDTH" "$HEIGHT" >/dev/null 2>&1 || true
fi

"$BIN" "${ARGS[@]}" open "$URL" >/dev/null 2>&1 || die "could not open $URL"

if [ "$DARK" = 1 ]; then
  "$BIN" "${ARGS[@]}" set media dark >/dev/null 2>&1 || true
  "$BIN" "${ARGS[@]}" set viewport "$WIDTH" "$HEIGHT" >/dev/null 2>&1 || true
fi

"$BIN" "${ARGS[@]}" wait "$WAIT" >/dev/null 2>&1 || sleep 1

if [ "$FULL" = 1 ]; then
  "$BIN" "${ARGS[@]}" screenshot "$OUT" --full >/dev/null 2>&1 \
    || "$BIN" "${ARGS[@]}" screenshot "$OUT" >/dev/null 2>&1 \
    || die "screenshot failed"
else
  "$BIN" "${ARGS[@]}" screenshot "$OUT" >/dev/null 2>&1 || die "screenshot failed"
fi

[ -s "$OUT" ] || die "screenshot is empty: $OUT"
echo "$OUT"
