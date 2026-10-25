#!/usr/bin/env bash
# render-deck.sh — render a generated deck to PNG (per slide) and/or a 16:9 PDF.
#
#   render-deck.sh <build-dir> [--png] [--pdf <out.pdf>] [--slides 1,3,5]
#                              [--width 1920] [--height 1080]
#
# PNG  : headless Linux chromium (agent-browser-local) — invisible, exact 1920×1080 viewport.
# PDF  : Windows Chrome (headless) — it is the only local engine that honours
#        `@page { size: 13.333in 7.5in }`; agent-browser/playwright falls back to Letter.
#        The print HTML is self-contained, so staging it in the Windows temp dir is enough.
#
# Inputs are produced by make-deck.py: <build>/slides/NN.html and <build>/deck-print.html.
# Exit 0 ok, 1 usage/tool error, 2 render error.

set -euo pipefail

BIN="${AGENT_BROWSER_BIN:-$HOME/.local/bin/agent-browser-local}"
CHROME="${DECK_CHROME:-/mnt/c/Program Files/Google/Chrome/Application/chrome.exe}"
WIN_TMP="${DECK_WIN_TMP:-/mnt/c/Users/pc/AppData/Local/Temp}"

die() { echo "render-deck.sh: $*" >&2; exit 1; }

BUILD=""
WANT_PNG=0
PDF_OUT=""
ONLY=""
WIDTH=1920
HEIGHT=1080

while [ $# -gt 0 ]; do
  case "$1" in
    --png)     WANT_PNG=1; shift ;;
    --pdf)     PDF_OUT="${2:-}"; shift 2 ;;
    --slides)  ONLY="${2:-}"; shift 2 ;;
    --width)   WIDTH="$2"; shift 2 ;;
    --height)  HEIGHT="$2"; shift 2 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *) [ -z "$BUILD" ] && BUILD="$1" || die "unexpected argument: $1"; shift ;;
  esac
done

[ -n "$BUILD" ] || die "usage: render-deck.sh <build-dir> [--png] [--pdf out.pdf]"
[ -d "$BUILD/slides" ] || die "no slides/ in $BUILD — run make-deck.py first"
[ "$WANT_PNG" = 1 ] || [ -n "$PDF_OUT" ] || die "nothing to do: pass --png and/or --pdf"

BUILD="$(cd "$BUILD" && pwd)"

wanted() {  # nn already zero-padded 2
  [ -z "$ONLY" ] && return 0
  case ",$ONLY," in
    *",$(printf '%02d' "$((10#$1))"),"*) return 0 ;;
    *) return 1 ;;
  esac
}

# ── PNG per slide ────────────────────────────────────────────────────────────
if [ "$WANT_PNG" = 1 ]; then
  [ -x "$BIN" ] || die "agent-browser not found at $BIN (set AGENT_BROWSER_BIN)"
  mkdir -p "$BUILD/png"
  SESSION="deck-$$"
  trap '"$BIN" --session "$SESSION" close >/dev/null 2>&1 || true' EXIT
  "$BIN" --session "$SESSION" set viewport "$WIDTH" "$HEIGHT" >/dev/null 2>&1 || true
  count=0
  for f in "$BUILD"/slides/*.html; do
    n="$(basename "$f" .html)"
    wanted "$n" || continue
    out="$BUILD/png/$n.png"
    "$BIN" --session "$SESSION" open "file://$f" >/dev/null 2>&1 || die "cannot open $f"
    "$BIN" --session "$SESSION" wait 400 >/dev/null 2>&1 || sleep 0.6
    "$BIN" --session "$SESSION" screenshot "$out" >/dev/null 2>&1 || die "screenshot failed: $n"
    [ -s "$out" ] || die "empty screenshot: $out"
    count=$((count + 1))
  done
  echo "render-deck.sh: $count PNG → $BUILD/png"
fi

# ── PDF (Windows Chrome honours @page size) ─────────────────────────────────
if [ -n "$PDF_OUT" ]; then
  print_html="$BUILD/deck-print.html"
  [ -f "$print_html" ] || die "missing $print_html (run make-deck.py)"
  if [ ! -x "$CHROME" ]; then
    echo "render-deck.sh: chrome not found at $CHROME — PDF skipped" >&2
    exit 1
  fi
  [ -d "$WIN_TMP" ] || die "Windows temp not reachable: $WIN_TMP"
  stage="$WIN_TMP/deck-pdf-$$"
  mkdir -p "$stage"
  cp "$print_html" "$stage/deck-print.html"
  win_out="$(wslpath -w "$stage/deck-print.html" | sed 's#deck-print\.html$#deck.pdf#')"
  "$CHROME" --headless=new --disable-gpu --no-sandbox --virtual-time-budget=15000 \
    --print-to-pdf="$win_out" "file:///$(wslpath -m "$stage/deck-print.html")" >/dev/null 2>&1 || true
  if [ ! -f "$stage/deck.pdf" ]; then
    rm -rf "$stage"
    die "chrome produced no PDF (check that the window is closed and chrome can start)"
  fi
  mkdir -p "$(dirname "$PDF_OUT")"
  cp "$stage/deck.pdf" "$PDF_OUT"
  rm -rf "$stage"
  size="$(du -h "$PDF_OUT" | cut -f1)"
  echo "render-deck.sh: PDF → $PDF_OUT ($size)"
fi
