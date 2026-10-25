#!/usr/bin/env bash
# page-check.sh — headless, vision-free layout & accessibility check of a rendered page.
#
#   page-check.sh <url|file> [--width 1440] [--height 900] [--wait <ms>] [--json]
#
# Measures the real geometry in a browser and reports: horizontal overflow, elements
# escaping the viewport, text under 14px, WCAG contrast failures, heading-order skips,
# images without alt, and interactive elements with no accessible name.
#
# Why this exists: the screenshot review in references/review-rubric.md needs a
# vision-capable model. This script is the mechanical half, so a text-only model can still
# verify a page instead of guessing. Run both when you can.
#
# Exit 0 = no HIGH/MED findings, 1 = findings, 2 = usage/browser error.

set -euo pipefail

BIN="${AGENT_BROWSER_BIN:-$HOME/.local/bin/agent-browser-local}"
URL=""
WIDTH=1440
HEIGHT=900
WAIT=900
JSON_OUT=0
SESSION=""

die() { echo "page-check.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --width)  WIDTH="$2"; shift 2 ;;
    --height) HEIGHT="$2"; shift 2 ;;
    --wait)   WAIT="$2"; shift 2 ;;
    --json)   JSON_OUT=1; shift ;;
    --session) SESSION="$2"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *) [ -z "$URL" ] && URL="$1" || die "unexpected argument: $1"; shift ;;
  esac
done

[ -n "$URL" ] || die "usage: page-check.sh <url|file> [--width N]"
[ -x "$BIN" ] || die "agent-browser not found at $BIN (set AGENT_BROWSER_BIN)"

case "$URL" in
  http://*|https://*|file://*) : ;;
  *) [ -f "$URL" ] || die "no such file: $URL"; URL="file://$(realpath "$URL")" ;;
esac

[ -n "$SESSION" ] || SESSION="chk-$$"
cleanup() { "$BIN" --session "$SESSION" close >/dev/null 2>&1 || true; }
trap cleanup EXIT

JS="$(mktemp /tmp/opencode/pagecheck-XXXX.js)"
RAW_JSON="$(mktemp /tmp/opencode/pagecheck-XXXX.json)"
trap 'rm -f "$JS" "$RAW_JSON"; cleanup' EXIT
cat > "$JS" <<'JSEOF'
const parseRGB = (s) => {
  const m = String(s || "").match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const p = m[1].split(",").map((x) => parseFloat(x));
  return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
};
const lum = (c) => {
  const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
};
const contrast = (a, b) => {
  const l1 = lum(a), l2 = lum(b);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};
const bgOf = (el) => {
  let n = el;
  while (n && n.nodeType === 1) {
    const st = getComputedStyle(n);
    const c = parseRGB(st.backgroundColor);
    if (c && c.a > 0.85) return c;
    n = n.parentElement;
  }
  return { r: 255, g: 255, b: 255, a: 1 };
};
const visible = (el, st) =>
  st.display !== "none" && st.visibility !== "hidden" &&
  parseFloat(st.opacity) > 0.05 && el.getClientRects().length > 0;
const hasOwnText = (el) => {
  for (const n of el.childNodes) {
    if (n.nodeType === 3 && n.textContent.trim().length > 1) return true;
  }
  return false;
};
/* 접근 가능한 이름: aria-label/title/alt → 자체 텍스트 → 연결된 <label> → 감싼 <label>.
 * label 연결을 빼먹으면 정상적인 폼이 전부 "이름 없음"으로 오탐된다. */
const accessibleName = (el) => {
  const direct = (el.getAttribute("aria-label") || el.getAttribute("title") ||
                  el.getAttribute("alt") || "").trim();
  if (direct) return direct;
  const own = (el.textContent || "").trim();
  if (own) return own;
  if (el.labels && el.labels.length) {
    const fromLabels = Array.from(el.labels)
      .map((l) => l.textContent.trim()).filter(Boolean).join(" ").trim();
    if (fromLabels) return fromLabels;
  }
  const id = el.getAttribute("id");
  if (id) {
    let escaped = id;
    try { escaped = CSS.escape(id); } catch (e) { escaped = id; }
    const lab = document.querySelector('label[for="' + escaped + '"]');
    if (lab && lab.textContent.trim()) return lab.textContent.trim();
  }
  return "";
};
const isDecorative = (el) => {
  let n = el;
  while (n && n.nodeType === 1) {
    if (n.getAttribute && n.getAttribute("aria-hidden") === "true") return true;
    n = n.parentElement;
  }
  return false;
};
const path = (el) => {
  const bits = [];
  let n = el;
  for (let i = 0; i < 4 && n && n.nodeType === 1; i++) {
    let s = n.tagName.toLowerCase();
    if (n.id) { s += "#" + n.id; bits.unshift(s); break; }
    if (n.classList && n.classList.length) s += "." + String(n.classList[0]);
    bits.unshift(s);
    n = n.parentElement;
  }
  return bits.join(" > ");
};

const vw = window.innerWidth;
/* 좌우 여백 기준 — SKILL.md '좌우 여백' 절. 폰 20px, 태블릿 24px, 데스크톱 5vw(최소 32px). */
const needPad = vw <= 480 ? 28 : vw <= 900 ? 36 : Math.max(40, vw * 0.045);
const INLINE_TAGS = /^(a|span|em|strong|b|i|u|code|small|label|abbr|time|br)$/;
const vh = window.innerHeight;
const out = {
  title: document.title,
  viewport: { w: vw, h: vh },
  pageWidth: document.documentElement.scrollWidth,
  pageHeight: document.documentElement.scrollHeight,
  horizontalOverflow: document.documentElement.scrollWidth - vw,
  overflowing: [],
  tight: [],
  smallText: [],
  contrast: [],
  headings: [],
  imagesWithoutAlt: 0,
  unnamedInteractive: [],
  koreanBreaks: [],
  markdownLeaks: [],
  imagesTotal: 0,
  elements: 0,
};

const all = document.querySelectorAll("body *");
out.elements = all.length;

/* 한글 어절이 줄바꿈에서 쪼개졌는지('독일' → '독/일') — 문자별 rect 의 top 비교 */
(() => {
  const isH = (c) => /[\uAC00-\uD7A3]/.test(c);
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  const r = document.createRange();
  while ((node = w.nextNode())) {
    const t = node.nodeValue;
    if (!t || !/[\uAC00-\uD7A3]/.test(t)) continue;
    if (out.koreanBreaks.length >= 5) break;
    for (let i = 0; i < t.length - 1; i++) {
      if (!isH(t[i]) || !isH(t[i + 1])) continue;
      try {
        r.setStart(node, i); r.setEnd(node, i + 1);
        const a = r.getBoundingClientRect();
        r.setStart(node, i + 1); r.setEnd(node, i + 2);
        const b = r.getBoundingClientRect();
        if (Math.abs(b.top - a.top) > 4) {
          out.koreanBreaks.push({ pair: t[i] + '/' + t[i + 1],
            ctx: t.slice(Math.max(0, i - 8), i + 9).replace(/\s+/g, ' ').trim() });
          i++;
        }
      } catch (e) { /* range 오류는 무시 */ }
    }
  }
})();

/* 마크다운 문법이 화면에 그대로 보이는지 — `**굵게**` 가 별표로 보이면 실패다. */
(() => {
  const PATTERNS = [
    [/\*\*[^*\n]{1,140}\*\*/g, 'bold', 'high'],
    [/(?<![\w*])\*[^*\n\s][^*\n]{0,80}\*(?![\w*])/g, 'italic', 'med'],
    [/`[^`\n]{1,120}`/g, 'code', 'high'],
    [/\[[^\]\n]{1,80}\]\([^)\n]{1,140}\)/g, 'link', 'high'],
    [/~~[^~\n]{1,80}~~/g, 'strike', 'med'],
    [/^\s{0,3}#{1,6}\s+\S/gm, 'heading', 'high'],
    [/^\s*\|[^\n]*\|[^\n]*\|/gm, 'table', 'med'],
  ];
  const skip = (node) => {
    for (let n = node.parentElement; n; n = n.parentElement) {
      const t = n.tagName;
      if (t === 'PRE' || t === 'CODE' || t === 'SCRIPT' || t === 'STYLE' || t === 'TEXTAREA') return true;
      if (n.classList && (n.classList.contains('md') || n.classList.contains('markdown'))) return true;
    }
    return false;
  };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = w.nextNode())) {
    if (out.markdownLeaks.length >= 6) break;
    const t = node.nodeValue;
    if (!t || t.trim().length < 4) continue;
    if (skip(node)) continue;
    for (const [rx, kind, sev] of PATTERNS) {
      rx.lastIndex = 0;
      const m = rx.exec(t);
      if (m) {
        out.markdownLeaks.push({ kind, sev,
          sample: t.slice(Math.max(0, m.index - 12), m.index + m[0].length + 12)
                     .replace(/\s+/g, ' ').trim() });
        break;
      }
    }
  }
})();

out.wordBreak = getComputedStyle(document.body).wordBreak;

for (const el of all) {
  const st = getComputedStyle(el);
  if (!visible(el, st)) continue;
  const r = el.getBoundingClientRect();
  const tag = el.tagName.toLowerCase();

  if (out.overflowing.length < 12 &&
      r.width > 0 && (r.right > vw + 2 || r.left < -2)) {
    out.overflowing.push({ el: path(el), left: Math.round(r.left), right: Math.round(r.right) });
  }

  if (hasOwnText(el)) {
    const fs = parseFloat(st.fontSize);
    const text = el.textContent.trim().replace(/\s+/g, " ");
    if (fs < 14 && text.length >= 16 && out.smallText.length < 12) {
      out.smallText.push({ el: path(el), px: fs, text: text.slice(0, 50) });
    }
    /* 본문이 화면 끝에 붙었는지 — 인라인 요소와 표 셀 내부는 부모가 판단한다 */
    if (!INLINE_TAGS.test(tag) && !el.closest("table") && out.tight.length < 8 &&
        r.left >= -1 && r.left < needPad - 1 && r.width > 0) {
      out.tight.push({ el: path(el), left: Math.round(r.left), need: Math.round(needPad),
                       text: text.slice(0, 40) });
    }
    const fg = parseRGB(st.color);
    if (fg && fg.a > 0.5) {
      const weight = parseInt(st.fontWeight, 10) || 400;
      const large = fs >= 24 || (fs >= 18.66 && weight >= 700);
      const need = large ? 3 : 4.5;
      const cr = contrast(fg, bgOf(el));
      if (cr < need - 0.05 && out.contrast.length < 12) {
        out.contrast.push({ el: path(el), ratio: Math.round(cr * 100) / 100,
                            need, px: fs, text: text.slice(0, 40) });
      }
    }
  }

  if (/^h[1-6]$/.test(tag)) out.headings.push({ level: +tag[1], text: el.textContent.trim().slice(0, 40) });

  if (tag === "img") {
    out.imagesTotal++;
    if (!el.hasAttribute("alt")) out.imagesWithoutAlt++;
  }

  if (["button", "a", "input", "select", "textarea"].includes(tag) ||
      el.getAttribute("role") === "button") {
    if (tag === "input" && ["hidden", "submit", "button", "reset", "image"].includes(el.type)) continue;
    if (isDecorative(el)) continue;
    const name = accessibleName(el);
    if (!name && out.unnamedInteractive.length < 12) out.unnamedInteractive.push(path(el));
  }
}

out;
JSEOF

ARGS=(--session "$SESSION")
"$BIN" "${ARGS[@]}" set viewport "$WIDTH" "$HEIGHT" >/dev/null 2>&1 || true
"$BIN" "${ARGS[@]}" open "$URL" >/dev/null 2>&1 || die "could not open $URL"
"$BIN" "${ARGS[@]}" wait "$WAIT" >/dev/null 2>&1 || sleep 1

RAW="$("$BIN" "${ARGS[@]}" eval --stdin --json < "$JS" 2>/dev/null || true)"
[ -n "$RAW" ] || die "eval returned nothing (page may have blocked the browser)"
printf '%s' "$RAW" > "$RAW_JSON"

if [ "$JSON_OUT" = 1 ]; then
  python3 - "$RAW_JSON" <<'PY'
import json, sys

def find_viewport(node):
    if isinstance(node, dict):
        if "viewport" in node and "horizontalOverflow" in node:
            return node
        for v in node.values():
            got = find_viewport(v)
            if got is not None:
                return got
    elif isinstance(node, list):
        for v in node:
            got = find_viewport(v)
            if got is not None:
                return got
    return None

data = find_viewport(json.load(open(sys.argv[1], encoding="utf-8")))
print(json.dumps(data, ensure_ascii=False, indent=2))
PY
fi

python3 - "$RAW_JSON" <<'PY'
import json, sys


def find_viewport(node):
    if isinstance(node, dict):
        if "viewport" in node and "horizontalOverflow" in node:
            return node
        for v in node.values():
            got = find_viewport(v)
            if got is not None:
                return got
    elif isinstance(node, list):
        for v in node:
            got = find_viewport(v)
            if got is not None:
                return got
    return None


raw = open(sys.argv[1], encoding="utf-8").read().strip()
try:
    data = find_viewport(json.loads(raw))
except Exception:
    print("page-check.sh: could not parse eval output:", raw[:300], file=sys.stderr)
    sys.exit(2)
if data is None:
    print("page-check.sh: unexpected eval shape:", raw[:300], file=sys.stderr)
    sys.exit(2)

high, med, low = [], [], []
vw = data["viewport"]["w"]

ho = data.get("horizontalOverflow", 0)
if ho > 1:
    high.append(f"가로 오버플로 {ho}px (page {data.get('pageWidth')}px vs viewport {vw}px)")
for o in data.get("overflowing", []):
    med.append(f"뷰포트 밖 요소 {o['el']} (left {o['left']}, right {o['right']})")

for t_ in data.get("tight", []):
    med.append(f"좌우 여백 부족 {t_['el']} — 본문이 left {t_['left']}px (기준 {t_['need']}px) — \"{t_['text']}\"")
for c in data.get("contrast", []):
    med.append(f"대비 부족 {c['ratio']}:1 (필요 {c['need']}) {c['px']:.0f}px — "
               f"{c['el']} — \"{c['text']}\"")
for s in data.get("smallText", []):
    low.append(f"작은 본문 {s['px']:.0f}px — {s['el']} — \"{s['text']}\"")
for lk in data.get("markdownLeaks", []):
    msg = f"마크다운 문법이 화면에 그대로 보임 [{lk['kind']}] — …{lk['sample']}…"
    (high if lk.get("sev") == "high" else med).append(msg)
for kb in data.get("koreanBreaks", []):
    med.append(f"한글 어절이 줄바꿈에서 쪼개짐 '{kb['pair']}' — …{kb['ctx']}… "
               f"(word-break: keep-all 필요)")
if data.get("wordBreak") and data["wordBreak"] != "keep-all" and data.get("koreanBreaks"):
    med.append(f"body word-break = {data['wordBreak']} — 한글은 keep-all 이어야 한다")
if data.get("imagesWithoutAlt"):
    med.append(f"alt 없는 이미지 {data['imagesWithoutAlt']}개 (총 {data.get('imagesTotal', 0)}개)")
for u in data.get("unnamedInteractive", []):
    med.append(f"접근 가능한 이름 없는 컨트롤: {u}")

prev = 0
for h in data.get("headings", []):
    lv = h["level"]
    if prev and lv > prev + 1:
        med.append(f"제목 계층 건너뜀 h{prev} → h{lv}")
        break
    prev = lv
if not data.get("headings"):
    low.append("h1~h6 제목이 하나도 없음")

print(f"page-check — {data.get('title')!r} · {vw}×{data['viewport']['h']}px · "
      f"elements {data.get('elements', 0)} · page height {data.get('pageHeight', 0)}px")
for label, items in (("HIGH", high), (" MED", med), (" LOW", low)):
    for it in items:
        print(f"{label}  {it}")
print(f"page-check: {len(high)} HIGH · {len(med)} MED · {len(low)} LOW")
print("  note: geometry/contrast only — composition, hierarchy and taste need the "
      "screenshot review.")
sys.exit(1 if (high or med) else 0)
PY
