#!/usr/bin/env bash
# deck-check.sh — per-slide geometry and density check for a generated deck.
#
#   deck-check.sh <build-dir> [--json] [--quiet] [--slides 1,3,5]
#
# For every build/slides/NN.html it measures, in a real 1920×1080 viewport:
#   · content overflow  — does the text run past the stage bottom? (HIGH: it will be cut)
#   · elements outside the stage box
#   · font sizes       — below 20px is HIGH, 20–27px on long text is MED
#   · text density     — slide text longer than 420 chars, or more than 5 bullets (MED)
#   · contrast         — body text under 4.5:1 (MED)
#   · empty slides     — a slide with a title but no body and no figure (MED)
#
# This is the mechanical half of the deck review. It cannot judge whether the argument is good —
# that is references/deck-architecture.md + the parent's review rubric.
#
# Exit 0 = clean, 1 = findings, 2 = usage/tool error.

set -euo pipefail

BIN="${AGENT_BROWSER_BIN:-$HOME/.local/bin/agent-browser-local}"
BUILD=""
JSON=0
QUIET=0
ONLY=""

die() { echo "deck-check.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --json)    JSON=1; shift ;;
    --quiet)   QUIET=1; shift ;;
    --slides)  ONLY="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *) [ -z "$BUILD" ] && BUILD="$1" || die "unexpected argument: $1"; shift ;;
  esac
done

[ -n "$BUILD" ] || die "usage: deck-check.sh <build-dir>"
[ -d "$BUILD/slides" ] || die "no slides/ in $BUILD — run make-deck.py first"
[ -x "$BIN" ] || die "agent-browser not found at $BIN (set AGENT_BROWSER_BIN)"
BUILD="$(cd "$BUILD" && pwd)"

wanted() {
  [ -z "$ONLY" ] && return 0
  case ",$ONLY," in *",$(printf '%02d' "$((10#$1))"),"*) return 0 ;; *) return 1 ;; esac
}

JS="$(mktemp /tmp/opencode/deckcheck-XXXX.js)"
OUT="$(mktemp /tmp/opencode/deckcheck-XXXX.jsonl)"
SESSION="deckchk-$$"
trap 'rm -f "$JS" "$OUT"; "$BIN" --session "$SESSION" close >/dev/null 2>&1 || true' EXIT

cat > "$JS" <<'JSEOF'
const parseRGB = (s) => {
  const m = String(s || "").match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const p = m[1].split(",").map(parseFloat);
  return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
};
const lum = (c) => { const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b); };
const contrast = (a, b) => { const l1 = lum(a), l2 = lum(b);
  return (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05); };
const bgOf = (el) => { let n = el;
  while (n && n.nodeType === 1) { const c = parseRGB(getComputedStyle(n).backgroundColor);
    if (c && c.a > 0.85) return c; n = n.parentElement; }
  return { r: 255, g: 255, b: 255, a: 1 }; };

const slide = document.querySelector(".slide");
const vw = window.innerWidth, vh = window.innerHeight;
const res = { title: document.title, index: slide ? slide.getAttribute("data-index") : null,
  overflowPx: 0, outside: [], smallFont: [], tinyFont: [], contrast: [], chars: 0,
  bullets: 0, emptyish: false };

if (slide) {
  res.overflowPx = Math.max(0, slide.scrollHeight - vh);
  const body = slide.querySelector(".slide__body");
  if (body) res.overflowPx = Math.max(res.overflowPx, body.scrollHeight - body.clientHeight + 2);
  res.chars = (slide.innerText || "").replace(/\s+/g, " ").trim().length;
  res.bullets = slide.querySelectorAll(".bullets li").length;
  const hasFigure = !!slide.querySelector(".slide__figure, .kpis, .chart, .tbl, .cmp, .quote, .tl, .flow");
  const hasBody = !!body;
  if (!hasFigure && !hasBody && slide.querySelector(".slide__title")) res.emptyish = true;

  const skip = (el) => {
    const st = getComputedStyle(el);
    return st.display === "none" || st.visibility === "hidden" || parseFloat(st.opacity) < 0.05;
  };
  for (const el of slide.querySelectorAll("*")) {
    if (skip(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.bottom > vh + 2 || r.right > vw + 2 || r.top < -2 || r.left < -2)) {
      if (res.outside.length < 10) res.outside.push({
        el: el.tagName.toLowerCase() + (el.className ? "." + String(el.className).split(" ")[0] : ""),
        bottom: Math.round(r.bottom), right: Math.round(r.right) });
    }
    let own = "";
    for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.trim();
    if (!own) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    const fg = parseRGB(getComputedStyle(el).color);
    const tag = el.tagName.toLowerCase() + (el.className ? "." + String(el.className).split(" ")[0] : "");
    /* 캡션·각주·표·도표 라벨은 작은 크기가 정상이다 (20px 이상이면 HIGH 아님). */
    const isCaption = !!el.closest(".slide__source, .slide__num, .cover__event, .slide__kicker, " +
      ".tl__meta, .kpi__label, .chart__label, .tbl, .cmp__col, .quote cite, .cover__who, figcaption");
    if (fs < 20) { if (res.tinyFont.length < 8) res.tinyFont.push({ el: tag, px: fs, text: own.slice(0, 30) }); }
    else if (fs < 28 && own.length >= 20 && !isCaption) {
      if (res.smallFont.length < 8) res.smallFont.push({ el: tag, px: fs, text: own.slice(0, 30) });
    }
    if (fg && fg.a > 0.5) {
      const weight = parseInt(getComputedStyle(el).fontWeight, 10) || 400;
      const need = (fs >= 32 || (fs >= 24 && weight >= 700)) ? 3 : 4.5;
      const cr = contrast(fg, bgOf(el));
      if (cr < need - 0.05 && res.contrast.length < 8) {
        res.contrast.push({ el: tag, ratio: Math.round(cr * 100) / 100, need, px: fs, text: own.slice(0, 24) });
      }
    }
  }
}
res;
JSEOF

"$BIN" --session "$SESSION" set viewport 1920 1080 >/dev/null 2>&1 || true

: > "$OUT"
for f in "$BUILD"/slides/*.html; do
  n="$(basename "$f" .html)"
  wanted "$n" || continue
  "$BIN" --session "$SESSION" open "file://$f" >/dev/null 2>&1 || die "cannot open $f"
  "$BIN" --session "$SESSION" wait 250 >/dev/null 2>&1 || sleep 0.4
  raw="$("$BIN" --session "$SESSION" eval --stdin --json < "$JS" 2>/dev/null || true)"
  printf '%s\n' "$raw" >> "$OUT"
done

python3 - "$OUT" "$BUILD" "$JSON" "$QUIET" <<'PY'
import json, sys
from pathlib import Path

raw_lines = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore").splitlines()
build, want_json, quiet = sys.argv[2], sys.argv[3] == "1", sys.argv[4] == "1"

def find(node):
    if isinstance(node, dict):
        if "overflowPx" in node and "chars" in node:
            return node
        for v in node.values():
            got = find(v)
            if got is not None:
                return got
    elif isinstance(node, list):
        for v in node:
            got = find(v)
            if got is not None:
                return got
    return None

results = []
for line in raw_lines:
    line = line.strip()
    if not line:
        continue
    try:
        r = find(json.loads(line))
    except Exception:
        r = None
    if r:
        results.append(r)

if not results:
    print("deck-check.sh: no slide measurements collected (browser blocked?)", file=sys.stderr)
    sys.exit(2)

findings = {"high": [], "med": [], "low": []}
def add(sev, slide_no, msg):
    findings[sev].append(f"slide {slide_no:0>2}: {msg}")

for r in results:
    no = r.get("index") or "?"
    if r["overflowPx"] > 2:
        add("high", no, f"내용이 스테이지를 {r['overflowPx']}px 넘침 — 잘린다")
    for o in r["outside"]:
        add("high", no, f"스테이지 밖 요소 {o['el']} (bottom {o['bottom']}, right {o['right']})")
    for t in r["tinyFont"]:
        add("high", no, f"폰트 {t['px']:.0f}px (<20px 최소치) — {t['el']} \"{t['text']}\"")
    for s in r["smallFont"]:
        add("med", no, f"폰트 {s['px']:.0f}px — 32px 권장 ({s['el']} \"{s['text']}\")")
    for c in r["contrast"]:
        add("med", no, f"대비 {c['ratio']}:1 (필요 {c['need']}) — {c['el']} \"{c['text']}\"")
    if r["chars"] > 420:
        add("med", no, f"텍스트 {r['chars']}자 — 발표용 상한 420자")
    if r["bullets"] > 5:
        add("med", no, f"불릿 {r['bullets']}개 — 5개 이하")
    if r["emptyish"]:
        add("med", no, "제목만 있고 본문·도표가 없음")

summary = {"slides": len(results), "high": len(findings["high"]),
           "med": len(findings["med"]), "low": len(findings["low"])}

if want_json:
    print(json.dumps({"summary": summary, "findings": findings,
                      "slides": [{"index": r.get("index"), "chars": r["chars"],
                                  "bullets": r["bullets"], "overflowPx": r["overflowPx"]}
                                 for r in results]}, ensure_ascii=False, indent=2))
else:
    print(f"deck-check — {len(results)} slides · {build}")
    for label, sev in (("HIGH", "high"), (" MED", "med"), (" LOW", "low")):
        if quiet and sev != "high":
            continue
        for f in findings[sev]:
            print(f"{label}  {f}")
    print(f"deck-check: {summary['high']} HIGH · {summary['med']} MED · {summary['low']} LOW")
    print("  note: geometry and density only — the argument quality needs deck-architecture.md.")

sys.exit(1 if (findings["high"] or findings["med"]) else 0)
PY
