#!/usr/bin/env python3
"""design-lint — scan a design surface for "AI slop" signals and non-token hardcoded values.

    design-lint.py <path> [<path> ...] [--tokens <tokens.css>] [--json]
                   [--fail-on high|med|low|never] [--quiet]

<path> may be a file or a directory (walked, with the usual build/vendor dirs skipped).

What it can and cannot do
-------------------------
It catches *mechanical* signals: default font families, the violet/indigo gradient
fingerprint, uniform radii and big shadows, glassmorphism, `transition: all`,
`outline: none` without a focus replacement, Lorem ipsum, marketing filler, un-tokenised
colors, and missing `prefers-reduced-motion`. It does NOT judge taste, hierarchy, spacing
rhythm or composition — that is what the screenshot review in `references/review-rubric.md`
is for. A clean run here means "no known fingerprint", not "good design".

Exit code: 0 normally, 1 when a finding at or above `--fail-on` exists (default: high).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# .svg files are (mostly) downloaded image assets — their inline font/colour literals are the
# original artist's, not our design decisions. Inline SVG inside HTML/CSS is still scanned.
DEFAULT_EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts",
                ".tsx", ".vue", ".svelte", ".astro", ".md", ".mdx"}
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", "out", "vendor", "coverage",
             ".cache", ".venv", "venv", "__pycache__", ".turbo", ".svelte-kit", ".output",
             "storybook-static", "public/build"}

# ── signal tables ────────────────────────────────────────────────────────────
DEFAULT_FONTS = {  # HIGH: the model did not choose a font
    "HIGH": ["inter", "roboto", "arial", "helvetica", "system-ui", "-apple-system",
             "blinkmacsystemfont", "segoe ui", "noto sans"],
    # MED: the standard issue of 2020-2024 AI output
    "MED": ["poppins", "montserrat", "lato", "open sans", "space grotesk", "nunito",
            "raleway", "ubuntu", "quicksand", "source sans", "work sans", "manrope"],
}

AI_PURPLE = ["#8b5cf6", "#6366f1", "#a855f7", "#7c3aed", "#4f46e5", "#a78bfa", "#818cf8",
             "#c084fc", "#e879f9", "#d946ef", "#9333ea", "#7e22ce", "#5b21b6", "#6d28d9"]
AI_GRADIENT_CLASSES = re.compile(
    r"(bg-gradient|linear-gradient)[^\n]{0,120}?"
    r"(from-(purple|violet|indigo|fuchsia)|to-(purple|violet|indigo)|#(8b5cf6|6366f1|a855f7|7c3aed|4f46e5))",
    re.I)
FILLER_COPY = re.compile(
    r"\b(seamless(ly)?|empower(ing)?|cutting[- ]edge|revolutionar(y|ize)|game[- ]chang(er|ing)|"
    r"next[- ]generation|state[- ]of[- ]the[- ]art|unlock the power|supercharge|"
    r"effortless(ly)?|world[- ]class)\b", re.I)
FILLER_COPY_KO = re.compile(r"혁신적|차세대|최첨단|압도적|무한한 가능성|새로운 차원|완벽한 솔루션")
LOREM = re.compile(r"lorem ipsum|dolor sit amet|consectetur adipiscing", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
RADIUS = re.compile(r"border-radius\s*:\s*([0-9.]+)(px|rem)", re.I)
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I | re.S)

SEV_ORDER = {"high": 0, "med": 1, "low": 2}
SEV_ICON = {"high": "HIGH", "med": " MED", "low": " LOW"}


class Finding:
    __slots__ = ("sev", "path", "line", "rule", "msg", "hint")

    def __init__(self, sev, path, line, rule, msg, hint=""):
        self.sev, self.path, self.line = sev, path, line
        self.rule, self.msg, self.hint = rule, msg, hint

    def as_dict(self):
        return {"severity": self.sev, "file": str(self.path), "line": self.line,
                "rule": self.rule, "message": self.msg, "hint": self.hint}


def iter_files(paths: list[Path], exts: set[str]):
    for p in paths:
        if p.is_file():
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                f = Path(root) / name
                if f.suffix.lower() in exts:
                    yield f


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def token_values(tokens_file: Path | None) -> set[str]:
    if not tokens_file or not tokens_file.is_file():
        return set()
    text = tokens_file.read_text(encoding="utf-8", errors="ignore")
    return {h.lower() for h in HEX.findall(text)}


def scan_file(path: Path, findings: list[Finding], stats: dict, tokens: set[str],
              seen: dict):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    low = text.lower()
    stats["files"] += 1

    # fonts ------------------------------------------------------------------
    # Only the *primary* family decides the look; suffixes like `system-ui, sans-serif`
    # are legitimate fallbacks. So we parse declarations and inspect item 0.
    decl = re.compile(
        r"(?:font-family|--font[\w-]*)\s*:\s*([^;}\n]+)"
        r"|fontFamily\s*:\s*[\"'`]([^\"'`]+)[\"'`]")
    for m in decl.finditer(text):
        stack = (m.group(1) or m.group(2) or "").strip()
        if not stack or stack.startswith("var("):
            continue
        primary = stack.split(",")[0].strip().strip("\"'` ").lower()
        if not primary:
            continue
        for sev, fonts in DEFAULT_FONTS.items():
            if primary in fonts:
                findings.append(Finding(
                    sev.lower(), path, line_of(text, m.start()), "default-font",
                    f"기본 폰트를 1순위로 사용: '{primary}'",
                    "톤에 맞는 폰트를 고르고 display/body 페어를 만든다 "
                    "(references/ai-slop-antipatterns.md)"))
                stats["fonts"][primary] += 1
                break
        token_names = {f.lower() for f in DEFAULT_FONTS["HIGH"] + DEFAULT_FONTS["MED"]}
        parts = [p.strip().strip("\"'` ").lower() for p in stack.split(",") if p.strip()]
        if len(parts) > 1 and all(p in token_names or p in
                                  {"sans-serif", "serif", "monospace", "cursive", "ui-sans-serif",
                                   "ui-serif", "ui-monospace"} for p in parts):
            findings.append(Finding(
                "med", path, line_of(text, m.start()), "font-stack-default",
                f"폰트 스택이 기본값뿐: {stack[:60]}",
                "최소 한 개는 의도적으로 고른 폰트여야 한다"))

    # AI purple --------------------------------------------------------------
    for m in re.finditer("|".join(re.escape(h) for h in AI_PURPLE), low):
        findings.append(Finding(
            "high", path, line_of(text, m.start()), "ai-purple",
            f"보라/인디고 계열 색 '{m.group(0)}'",
            "AI 생성물 지문. 지배색+악센트 구조로 바꾼다"))
    for m in AI_GRADIENT_CLASSES.finditer(text):
        findings.append(Finding(
            "high", path, line_of(text, m.start()), "ai-gradient",
            "보라/인디고 그라디언트", "그라디언트는 배경 재질에만, 팔레트는 다시 정한다"))

    # pure black / white -----------------------------------------------------
    for m in re.finditer(r"(?:background(?:-color)?|color)\s*:\s*#(?:000|000000|fff|ffffff)\b",
                         low):
        findings.append(Finding(
            "med", path, line_of(text, m.start()), "pure-mono",
            "순수 #000/#fff", "웜톤/쿨톤 오프값(#1A1714, #FBFAF8)이 질감을 만든다"))

    # glassmorphism ----------------------------------------------------------
    if "backdrop-filter" in low or "-webkit-backdrop-filter" in low:
        i = low.find("backdrop-filter")
        findings.append(Finding(
            "med", path, line_of(text, i), "glassmorphism",
            "backdrop-filter (glassmorphism)",
            "2021년 유행 지문. 레이어·보더·대비로 층을 만든다"))

    # transition: all --------------------------------------------------------
    for m in re.finditer(r"transition\s*:\s*all", low):
        findings.append(Finding(
            "med", path, line_of(text, m.start()), "transition-all",
            "transition: all", "변하는 속성을 명시한다"))

    # radii ------------------------------------------------------------------
    for m in RADIUS.finditer(text):
        val = float(m.group(1))
        if 6 <= val <= 16 and m.group(2) == "px":
            stats["radii"][f"{m.group(1)}px"] += 1
            findings.append(Finding(
                "low", path, line_of(text, m.start()), "radius-uniform",
                f"border-radius {m.group(1)}px",
                "반경을 sm/md/pill 3단계로만 쓰고 균일 반복을 피한다"))

    # big generic shadows ----------------------------------------------------
    for m in re.finditer(r"(box-)?shadow-(md|lg|xl|2xl)\b|\bbox-shadow\s*:", text, re.I):
        stats["shadows"] += 1
        findings.append(Finding(
            "med", path, line_of(text, m.start()), "generic-shadow",
            f"일반 그림자 '{m.group(0)}'",
            "1px 보더 + 배경 대비가 더 세련되다. 그림자는 오버레이에만"))

    # focus removal ----------------------------------------------------------
    if re.search(r"outline\s*:\s*(none|0)", low) and "focus-visible" not in low and \
       ":focus" not in low:
        i = re.search(r"outline\s*:\s*(none|0)", low).start()
        findings.append(Finding(
            "high", path, line_of(text, i), "focus-removed",
            "outline 제거 후 focus 대체 스타일 없음",
            ":focus-visible 링을 반드시 넣는다 (접근성)"))

    # reduced motion (aggregate later) --------------------------------------
    if "prefers-reduced-motion" in low:
        seen["reduced_motion"] = True
    if re.search(r"@keyframes|animation\s*:|transition\s*:", low):
        seen["has_motion"] = True

    # emoji as icons ---------------------------------------------------------
    for m in EMOJI.finditer(text):
        findings.append(Finding(
            "med", path, line_of(text, m.start()), "emoji-icon",
            f"이모지 사용 '{m.group(0)}'",
            "아이콘 세트를 정하거나 아예 뺀다"))
        break

    # hardcoded value budget -------------------------------------------------
    hexes = HEX.findall(text)
    if hexes:
        stats["hex"] += len(hexes)
        if tokens:
            off = [h for h in hexes if h.lower() not in tokens]
            if off:
                findings.append(Finding(
                    "med", path, 1, "color-off-token",
                    f"토큰에 없는 hex {len(off)}개 (예: {off[0]})",
                    "색은 tokens.css 한 곳에서만 정의한다"))
        elif path.suffix.lower() in {".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"} \
                and len(hexes) >= 3:
            findings.append(Finding(
                "med", path, 1, "color-hardcoded",
                f"컴포넌트에 hex {len(hexes)}개",
                "CSS 변수(tokens)로 옮긴다"))

    # lorem / filler copy ----------------------------------------------------
    for rx, rule, hint in ((LOREM, "lorem", "플레이스홀더를 실제 카피로 대체"),
                           (FILLER_COPY, "filler-copy", "구체적 사실·수치로 다시 쓴다")):
        m = rx.search(text)
        if m:
            findings.append(Finding(
                "high" if rule == "lorem" else "med", path, line_of(text, m.start()),
                rule, f"빈 문장/플레이스홀더 '{m.group(0)[:40]}'", hint))
    m = FILLER_COPY_KO.search(text)
    if m:
        findings.append(Finding(
            "med", path, line_of(text, m.start()), "filler-copy-ko",
            f"빈 문장 '{m.group(0)}'", "구체적 사실·수치로 다시 쓴다"))

    # img without alt --------------------------------------------------------
    for m in IMG_TAG.finditer(text):
        tag = m.group(0)
        if not re.search(r"\balt\s*=", tag, re.I):
            findings.append(Finding(
                "med", path, line_of(text, m.start()), "img-alt",
                "<img> 에 alt 없음", "alt 를 넣거나 장식이면 alt=\"\" 로 명시"))
            break

    # 100vh hero -------------------------------------------------------------
    for m in re.finditer(r"100vh", text):
        if "height" in low[max(0, m.start() - 30):m.start()] or "min-h" in \
                low[max(0, m.start() - 30):m.start()]:
            findings.append(Finding(
                "low", path, line_of(text, m.start()), "vh-hero",
                "100vh 고정 높이", "모바일 주소창 문제 — svh/dvh 사용"))
            break

    # un-tokenised font sizes ------------------------------------------------
    for m in re.finditer(r"font-size\s*:\s*(\d{2,3})px", low):
        stats["px_font"] += 1
        if float(m.group(1)) < 16 and not re.search(r"caption|label|badge|small",
                                                    low[max(0, m.start() - 60):m.start()]):
            findings.append(Finding(
                "low", path, line_of(text, m.start()), "tiny-font",
                f"font-size {m.group(1)}px (<16px)",
                "본문 최소 16px. 캡션·라벨이면 의도임을 주석으로 남긴다"))
            break


def aggregate(findings: list[Finding], stats: dict, seen: dict, paths):
    # uniform radius ---------------------------------------------------------
    if stats["radii"]:
        top, count = stats["radii"].most_common(1)[0]
        if count >= 5 and len(stats["radii"]) <= 2:
            findings.append(Finding(
                "high", paths[0], 0, "radius-monoculture",
                f"동일 반경 '{top}' 이 {count}회 — 반경 결정을 하지 않았다",
                "sm/md/pill 3단계로 나눈다 (AI 티 대표 신호)"))
    # missing reduced motion ------------------------------------------------
    if seen.get("has_motion") and not seen.get("reduced_motion"):
        findings.append(Finding(
            "med", paths[0], 0, "reduced-motion-missing",
            "모션/트랜지션이 있는데 prefers-reduced-motion 분기가 없다",
            "미디어 쿼리로 transform/animation 을 끈다"))
    # missing focus-visible anywhere ---------------------------------------
    if stats["files"] and not seen.get("focus"):
        findings.append(Finding(
            "low", paths[0], 0, "focus-visible-missing",
            ":focus-visible 스타일이 어디에도 없다",
            "키보드 사용자를 위해 포커스 링을 정의한다"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="design-lint — AI-slop signal scanner")
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--tokens", type=Path, default=None,
                    help="tokens.css — hex values here are treated as the allowed set")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["high", "med", "low", "never"], default="high")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    a = ap.parse_args(argv[1:])

    missing = [p for p in a.paths if not p.exists()]
    if missing:
        print(f"design-lint: no such path: {', '.join(str(m) for m in missing)}",
              file=sys.stderr)
        return 2

    tokens = token_values(a.tokens)
    findings: list[Finding] = []
    stats = {"files": 0, "hex": 0, "shadows": 0, "px_font": 0,
             "fonts": Counter(), "radii": Counter()}
    seen: dict = {}
    files = list(iter_files(a.paths, DEFAULT_EXTS))
    for f in files:
        scan_file(f, findings, stats, tokens, seen)
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "focus-visible" in txt or ":focus" in txt:
            seen["focus"] = True
    aggregate(findings, stats, seen, a.paths)

    findings.sort(key=lambda x: (SEV_ORDER[x.sev], str(x.path), x.line))

    if a.json:
        print(json.dumps({"files": stats["files"], "findings": [f.as_dict() for f in findings],
                          "stats": {"hex_literals": stats["hex"],
                                    "radii": dict(stats["radii"]),
                                    "font_families": dict(stats["fonts"]),
                                    "shadows": stats["shadows"],
                                    "px_font_sizes": stats["px_font"]}},
                         ensure_ascii=False, indent=2))
    else:
        counts = Counter(f.sev for f in findings)
        if not a.quiet:
            for f in findings:
                loc = f"{f.path}:{f.line}" if f.line else f"{f.path}:"
                print(f"{SEV_ICON[f.sev]}  {loc}  [{f.rule}] {f.msg}")
                if f.hint:
                    print(f"        → {f.hint}")
        print(f"\ndesign-lint: {stats['files']} files · "
              f"{counts['high']} HIGH · {counts['med']} MED · {counts['low']} LOW")
        print(f"  signals: {stats['hex']} hex · {stats['shadows']} shadows · "
              f"{len(stats['radii'])} radius values"
              + (f" · tokens: {len(tokens)} allowed hex" if tokens else
                 " · no --tokens (color check disabled)"))
        print("  note: this catches fingerprints only — the screenshot review decides quality.")

    if a.fail_on == "never":
        return 0
    worst = min((SEV_ORDER[f.sev] for f in findings), default=99)
    return 1 if worst <= SEV_ORDER[a.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
