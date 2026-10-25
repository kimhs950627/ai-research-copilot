#!/usr/bin/env python3
"""palette-advisor — 디자인 표면마다 **색을 새로 정하게** 강제하는 도구.

design-craft 는 표면(카드·덱·책·자료·사이트)마다 색을 다시 정한다. 이 스크립트가 그 결정을
결정적으로 도와준다: 주제·청중·매체·무드를 입력하면

  1. 색 계열(family) 후보를 점수로 줄 세우고 (키워드 적합도 + 매체 적합도 + 최근 사용 감점),
  2. 토큰 CSS 블록을 만들어 주고,
  3. WCAG 대비를 **실제로 계산해** PASS/FAIL 을 보고한다.

같은 입력은 같은 결과를 낸다(재현 가능). `--seed` 로 변주하고, 히스토리 파일에 최근 사용 계열을
기록해 "지난번과 같은 색"을 스스로 감지한다.

사용:
  P=~/.config/opencode/skills/design-craft/scripts/palette-advisor.py
  python3 $P --subject "가정의학과 건강검진 안내" --medium card --mood "차분한, 신뢰"
  python3 $P --subject "미국 주식 투자레터" --medium newsletter --json
  python3 $P --write /tmp/opencode/tokens.colors.css --subject "위내시경 전 처치" --medium deck
  python3 $P --list                     # 전체 계열 목록
  python3 $P --report tokens.css        # 기존 토큰 파일의 대비만 검사

종료 코드: 0 = PASS(모든 대비 통과) · 1 = FAIL(대비 미달) · 2 = 사용 오류.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HISTORY = Path(os.environ.get("DESIGN_CRAFT_PALETTE_HISTORY", Path.home() / ".cache/design-craft/palette-history.jsonl"))

MEDIA_PREFERS_PRINT_SAFE = {"book", "pdf", "print", "workbook", "cuecard", "study", "report"}

# ── 색 계산 ────────────────────────────────────────────────────────────────────


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"bad hex: {h!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(rgb: tuple[float, float, float] | tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def _lin(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = luminance(hex_to_rgb(a)), luminance(hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def rgba(hex_color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def fit_contrast(fg: str, bg: str, target: float, towards: str = "black") -> str:
    """fg 를 흰/검 쪽으로 섞어 bg 대비 target 을 만족하는 가장 가까운 색을 찾는다."""
    anchor = "#FFFFFF" if towards == "white" else "#000000"
    if contrast(fg, bg) >= target:
        return fg
    lo, hi = 0.0, 1.0
    best = mix(fg, anchor, 1.0)
    for _ in range(28):
        mid = (lo + hi) / 2
        cand = mix(fg, anchor, mid)
        if contrast(cand, bg) >= target:
            best, hi = cand, mid
        else:
            lo = mid
    return best


# ── 색 계열 카탈로그 ────────────────────────────────────────────────────────────
# surface0/1/2 = 표면 사다리, ink = 본문 잉크, accent[0] = 주 악센트, accent[1] = 같은 계열의
# 대안 악센트(씨앗에 따라 선택 → 같은 계열도 매번 같지는 않게).
FAMILIES: list[dict] = [
    {
        "name": "warm-clay",
        "ko": "따뜻한 점토",
        "hue": "warm",
        "moods": ["따뜻한", "정겨운", "손맛", "생활", "회고", "느린", "warm", "earthy"],
        "keywords": ["요리", "레시피", "음식", "식당", "카페", "맛", "장보기", "반찬", "가족", "부부", "살림",
                     "수공예", "도자기", "전통", "한옥", "노년", "어르신", "동네", "food", "recipe", "home"],
        "surfaces": ["#F4EFE8", "#E8E0D5", "#DED6CB"],
        "ink": "#17140F",
        "accent": ["#B33A0B", "#8A5A2B"],
        "print_safe": True,
    },
    {
        "name": "clinical-cool",
        "ko": "임상 쿨그레이 + 틸",
        "hue": "cool",
        "moods": ["청결한", "정확한", "차분한", "중립", "단정한", "clinical", "precise", "calm"],
        "keywords": ["의학", "임상", "검진", "병원", "외래", "진료", "처방", "약물", "증례", "내시경", "초음파",
                     "가이드라인", "논문", "데이터", "통계", "실험", "medical", "clinical", "data", "lab"],
        "surfaces": ["#F6F8F9", "#E7EDF0", "#D8E1E5"],
        "ink": "#0F171C",
        "accent": ["#0E7490", "#155E75"],
        "print_safe": True,
    },
    {
        "name": "deep-ink",
        "ko": "딥 네이비 잉크 + 황동",
        "hue": "neutral-dark",
        "moods": ["신뢰", "격식", "단호한", "분석적", "권위", "trust", "serious", "institutional"],
        "keywords": ["금융", "투자", "주식", "시장", "부동산", "세금", "법률", "계약", "정부", "기관", "보고서",
                     "이사회", "감사", "예산", "finance", "invest", "market", "legal", "policy", "report"],
        "surfaces": ["#F7F6F3", "#EAE7E0", "#DCD8CF"],
        "ink": "#101828",
        "accent": ["#A16207", "#1D4ED8"],
        "print_safe": True,
    },
    {
        "name": "forest-field",
        "ko": "포레스트 · 올리브",
        "hue": "green",
        "moods": ["자연", "건강한", "차분한", "지속가능", "활기찬", "natural", "healthy", "grounded"],
        "keywords": ["자연", "환경", "건강", "습관", "운동", "산책", "영양", "식이", "체중", "금연", "절주",
                     "수면", "웰빙", "농업", "숲", "여행", "등산", "health", "nature", "habit", "wellness"],
        "surfaces": ["#F5F6F1", "#E6E9DD", "#D7DCCB"],
        "ink": "#16201A",
        "accent": ["#16543A", "#3F6212"],
        "print_safe": True,
    },
    {
        "name": "oxblood-archive",
        "ko": "옥스블러드 · 아카이브",
        "hue": "red",
        "moods": ["문학적", "고전적", "편집", "무게감", "아카이브", "editorial", "literary", "archival"],
        "keywords": ["역사", "문학", "출판", "책", "교재", "원고", "고전", "다큐", "인문", "연구", "학회",
                     "연대기", "기록", "증례기록", "history", "literature", "book", "archive", "essay"],
        "surfaces": ["#F6F2EF", "#E9E1DC", "#DBD1CA"],
        "ink": "#1B1113",
        "accent": ["#8C1C1C", "#7C2D12"],
        "print_safe": True,
    },
    {
        "name": "plum-rose",
        "ko": "플럼 · 로즈 (낮은 채도)",
        "hue": "purple",
        "moods": ["섬세한", "사적인", "감성", "조용한", "intimate", "delicate", "quiet"],
        "keywords": ["마음", "정서", "상담", "심리", "돌봄", "수면", "통증", "회복", "일기", "신혼", "기념일",
                     "선물", "취미", "음악", "사진", "케어", "care", "mood", "diary"],
        "surfaces": ["#F8F4F7", "#EDE3EC", "#E0D3DE"],
        "ink": "#17111A",
        "accent": ["#9D174D", "#7A2E5A"],
        "print_safe": True,
    },
    {
        "name": "graphite-lime",
        "ko": "그래파이트 + 라임",
        "hue": "technical",
        "moods": ["기술적", "실험적", "날카로운", "빠른", "개발자", "technical", "experimental", "bold"],
        "keywords": ["코드", "개발", "엔지니어링", "AI", "모델", "데이터셋", "벤치마크", "API", "서버", "앱",
                     "소프트웨어", "배포", "성능", "code", "dev", "engineering", "AI", "model", "benchmark"],
        "surfaces": ["#F4F5F4", "#E4E6E4", "#D5D8D5"],
        "ink": "#101211",
        "accent": ["#4D7C0F", "#0F766E"],
        "print_safe": False,
    },
    {
        "name": "cobalt-paper",
        "ko": "코발트 · 페이퍼",
        "hue": "blue",
        "moods": ["현대적", "제품", "명료한", "모던", "modern", "product", "clear"],
        "keywords": ["제품", "서비스", "스타트업", "홈페이지", "랜딩", "웹", "SaaS", "도구", "플랫폼", "온보딩",
                     "가입", "구독", "product", "saas", "web", "landing", "platform"],
        "surfaces": ["#F5F7FB", "#E6EAF3", "#D5DCEA"],
        "ink": "#0B1220",
        "accent": ["#1D4ED8", "#0369A1"],
        "print_safe": False,
    },
    {
        "name": "sand-charcoal",
        "ko": "샌드 · 차콜 (실무·워크북)",
        "hue": "sand",
        "moods": ["실무적", "정돈된", "학습", "연습", "practical", "workbook", "study"],
        "keywords": ["워크북", "학습", "연습", "문제", "정리", "요약", "암기", "시험", "강의", "교안", "교육",
                     "매뉴얼", "체크리스트", "학습자료", "study", "workbook", "exam", "lecture", "checklist"],
        "surfaces": ["#FAF7F1", "#EDE7DB", "#DED5C4"],
        "ink": "#1A1A1A",
        "accent": ["#8A6A2F", "#9A3412"],
        "print_safe": True,
    },
    {
        "name": "slate-mint",
        "ko": "슬레이트 · 민트 (헬스케어 라이트)",
        "hue": "teal-green",
        "moods": ["부드러운", "회복", "안심", "친절한", "reassuring", "gentle", "supportive"],
        "keywords": ["재활", "간병", "요양", "예방접종", "검사 안내", "복약 안내", "생활습관", "금연", "절주",
                     "영양 상담", "산전", "소아", "어린이", "예방", "안내문", "patient", "screening", "care"],
        "surfaces": ["#F4F8F7", "#E2EDEA", "#D2E1DD"],
        "ink": "#0E1A18",
        "accent": ["#0F766E", "#15803D"],
        "print_safe": True,
    },
]

FAMILY_BY_NAME = {f["name"]: f for f in FAMILIES}

# design-lint.py 의 ai-purple 목록과 같은 값 — 생성 결과가 HIGH 를 만들면 안 된다.
AI_PURPLE = {"#8b5cf6", "#6366f1", "#a855f7", "#7c3aed", "#4f46e5", "#a78bfa", "#818cf8",
             "#c084fc", "#e879f9", "#d946ef", "#9333ea", "#7e22ce", "#5b21b6", "#6d28d9"}


# ── 점수화 ─────────────────────────────────────────────────────────────────────


def _seed_int(seed: str) -> int:
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12], 16)


def keyword_hits(family: dict, text: str) -> list[str]:
    low = text.lower()
    return [k for k in family["keywords"] + family["moods"] if k.lower() in low]


def recent_families(limit: int = 6) -> list[str]:
    if not HISTORY.exists():
        return []
    rows = []
    try:
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return []
    return [r.get("family", "") for r in rows[-limit:]]


def rank(subject: str, medium: str, mood: str, seed: str, exclude: set[str],
         penalize_recent: bool, force_family: str = "") -> list[dict]:
    text = f"{subject} {mood}"
    history = recent_families()
    seed_i = _seed_int(seed or subject or medium or force_family)
    out = []
    for i, fam in enumerate(FAMILIES):
        hits = keyword_hits(fam, text)
        score = 3.0 * len(hits)
        if medium in MEDIA_PREFERS_PRINT_SAFE and fam["print_safe"]:
            score += 2.0
        if medium in {"card", "sns", "site", "landing"} and not fam["print_safe"]:
            score += 1.0
        if fam["name"] in exclude:
            score -= 100.0
        if penalize_recent and fam["name"] in history:
            score -= 4.0 * history.count(fam["name"])
        if force_family:
            score = 999.0 if fam["name"] == force_family else -999.0
        accent = fam["accent"][(seed_i // (i + 1)) % len(fam["accent"])]
        out.append({"family": fam, "score": score, "hits": hits, "accent": accent})
    out.sort(key=lambda r: (-r["score"], (seed_i + FAMILIES.index(r["family"])) % 997))
    return out



# ── 토큰 생성 (대비를 실제로 맞춰서) ─────────────────────────────────────────────


def build_tokens(fam: dict, accent: str, medium: str) -> tuple[dict, list[dict]]:
    s0, s1, s2 = fam["surfaces"]
    ink = fam["ink"]
    checks: list[dict] = []
    worst = s2  # 가장 어두운 표면 = 진한 글자에 가장 불리한 배경. 이걸 기준으로 맞춘다.

    def check(label: str, fg: str, bg: str, target: float, towards: str = "black") -> str:
        fixed = fit_contrast(fg, bg, target, towards)
        ratio = contrast(fixed, bg)
        checks.append({"label": label, "fg": fixed, "bg": bg, "ratio": round(ratio, 2),
                       "target": target, "ok": ratio + 1e-9 >= target})
        return fixed

    text1 = check("text-1 on surface-2 (worst case)", ink, worst, 10.0)
    check("text-1 on surface-0", text1, s0, 10.0)
    text2 = check("text-2 on surface-2 (worst case)", mix(text1, worst, 0.32), worst, 5.0)
    check("text-2 on surface-0", text2, s0, 5.0)
    text3 = check("text-3 on surface-2 (worst case)", mix(text2, worst, 0.20), worst, 4.5)
    check("text-3 on surface-0", text3, s0, 4.5)
    ladder = (luminance(hex_to_rgb(text1)) <= luminance(hex_to_rgb(text2)) <= luminance(hex_to_rgb(text3)))
    checks.append({"label": "텍스트 명도 사다리 (text-1 ≤ text-2 ≤ text-3)", "fg": "-", "bg": "-",
                   "ratio": 0.0, "target": 0.0, "ok": ladder,
                   "note": f"{text1} / {text2} / {text3}"})
    inverse = ink
    on_inverse = check("on-inverse on inverse", s0, inverse, 4.5, "white")
    accent_fixed = fit_contrast(accent, worst, 4.5)
    check("accent as text on surface-2 (worst case)", accent_fixed, worst, 4.5)
    check("accent as text on surface-0", accent_fixed, s0, 4.5)
    on_accent = check("white on accent (버튼)", "#FFFFFF", accent_fixed, 4.5, "white")
    positive = check("positive on surface-2", "#2F6F4E", worst, 4.5)
    warning = check("warning on surface-2", "#9A6A00", worst, 4.5)
    negative = check("negative on surface-2", "#A32A2A", worst, 4.5)

    tokens = {
        "--color-surface-0": s0,
        "--color-surface-1": s1,
        "--color-surface-2": s2,
        "--color-surface-inverse": inverse,
        "--color-surface-overlay": rgba(inverse, 0.72),
        "--color-text-1": text1,
        "--color-text-2": text2,
        "--color-text-3": text3,
        "--color-text-on-inverse": on_inverse,
        "--color-text-on-accent": on_accent,
        "--color-border": rgba(text1, 0.14),
        "--color-border-strong": rgba(text1, 0.30),
        "--color-accent": accent_fixed,
        "--color-accent-quiet": mix(accent_fixed, s0, 0.84),
        "--color-accent-strong": fit_contrast(mix(accent_fixed, "#000000", 0.25), s0, 7.0),
        "--color-focus": mix("#1D4ED8", accent_fixed, 0.25),
        "--color-positive": positive,
        "--color-warning": warning,
        "--color-negative": negative,
    }
    banned = {v.upper() for v in tokens.values() if isinstance(v, str)} & AI_PURPLE
    checks.append({"label": "AI 보라/인디고 회피 (design-lint ai-purple)", "fg": "-", "bg": "-",
                   "ratio": 0.0, "target": 0.0, "ok": not banned,
                   "note": f"금지색 {sorted(banned)}" if banned else "금지색 없음"})
    return tokens, checks


def tokens_css(fam: dict, tokens: dict, accent: str, subject: str, medium: str) -> str:
    lines = [
        "/* design-craft — palette-advisor 로 생성한 색 토큰 (색만).",
        f" * 계열: {fam['name']} ({fam['ko']}) · 악센트 {accent} · 매체 {medium}",
        f" * 대상: {subject}",
        " * 타입·간격·모션 토큰은 design-tokens.template.css 에서 그대로 가져온다.",
        " * 이 블록을 토큰 파일의 :root 안에 병합한다(색 정의는 여기 한 곳에만).",
        " */",
        ":root {",
    ]
    for k, v in tokens.items():
        lines.append(f"  {k}: {v};")
    lines += [
        "}",
        "",
        "/* 인쇄(PDF·책)라면: 강조는 굵은 글씨·괘선으로도 표현하고, 색만으로 정보를 구분하지 않는다. */",
    ]
    return "\n".join(lines) + "\n"


# ── 기존 토큰 파일 검사 ──────────────────────────────────────────────────────────


def report_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    vals = dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", text))
    surfaces = [k for k in ("--color-surface-0", "--color-surface-1", "--color-surface-2") if k in vals]
    if not surfaces:
        surfaces = [k for k in vals if "surface" in k and "inverse" not in k][:1]
    failures = 0
    print(f"[palette report] {path}")
    for bg in surfaces:
        for fg in ("--color-text-1", "--color-text-2", "--color-text-3", "--color-accent"):
            if fg not in vals:
                continue
            ratio = contrast(vals[fg], vals[bg])
            need = 4.5
            ok = ratio + 1e-9 >= need
            failures += 0 if ok else 1
            print(f"  {'PASS' if ok else 'FAIL'}  {fg} on {bg}: {ratio:.2f}:1 (≥{need})")
    accent = vals.get("--color-accent")
    if accent:
        on_accent = vals.get("--color-text-on-accent", "#FFFFFF")
        r2 = contrast(on_accent, accent)
        ok = r2 + 1e-9 >= 4.5
        failures += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {on_accent} on accent: {r2:.2f}:1 (≥4.5)")
    for fam in FAMILIES:
        hit = next((c for c in fam["surfaces"] + [fam["ink"]] if c.upper() in text.upper()), "")
        if hit:
            print(f"  note   계열 흔적: {fam['name']} ({fam['ko']}) — {hit}")
            break
        hit = next((c for c in fam["accent"] if c.upper() in text.upper()), "")
        if hit:
            print(f"  note   계열 흔적(악센트): {fam['name']} ({fam['ko']}) — {hit}")
            break
    return 1 if failures else 0


# ── main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="표면에 맞는 색 계열을 골라 토큰을 만들고 대비를 검사한다")
    ap.add_argument("--subject", default="", help="무엇에 대한 산출물인가 (예: '가정의학과 건강검진 안내')")
    ap.add_argument("--medium", default="screen",
                    choices=["screen", "web", "site", "landing", "card", "sns", "deck", "pdf", "report", "book",
                             "workbook", "study", "cuecard", "newsletter", "illus", "motion"],
                    help="산출물 매체 (인쇄 계열은 print-safe 계열을 우선)")
    ap.add_argument("--mood", default="", help="원하는 무드·톤 (쉼표로 여러 개)")
    ap.add_argument("--seed", default="", help="변주 씨앗 (기본: subject)")
    ap.add_argument("--exclude", action="append", default=[], help="제외할 계열 이름 (반복 가능)")
    ap.add_argument("--family", choices=sorted(FAMILY_BY_NAME),
                    help="계열을 직접 지정한다 (주제 없이도 동작, 이미 정한 계열의 토큰만 뽑을 때)")
    ap.add_argument("--exclude-recent", action="store_true",
                    help="히스토리의 최근 계열을 감점(다른 색을 강제)")
    ap.add_argument("--top", type=int, default=3, help="보여줄 후보 수 (기본 3)")
    ap.add_argument("--write", metavar="PATH", help="1순위 토큰 CSS 를 이 경로에 쓴다")
    ap.add_argument("--record", action="store_true", help="1순위 계열을 히스토리에 기록")
    ap.add_argument("--json", action="store_true", help="JSON 으로 출력")
    ap.add_argument("--list", action="store_true", help="전체 계열 목록만 출력")
    ap.add_argument("--report", metavar="FILE", help="기존 토큰 CSS 의 대비만 검사")
    args = ap.parse_args(argv)

    if args.list:
        for fam in FAMILIES:
            print(f"{fam['name']:16s} {fam['ko']:28s} surface0={fam['surfaces'][0]} "
                  f"ink={fam['ink']} accent={fam['accent'][0]} print_safe={fam['print_safe']}")
        return 0

    if args.report:
        path = Path(args.report)
        if not path.exists():
            print(f"파일이 없다: {path}", file=sys.stderr)
            return 2
        return report_file(path)

    subject = args.subject.strip()
    if not subject and not args.mood and not args.family:
        print("--subject 또는 --mood 중 하나는 필요하다 (무엇을 위한 색인지 알 수 없다).", file=sys.stderr)
        return 2

    ranked = rank(subject, args.medium, args.mood, args.seed or subject, set(args.exclude),
                  args.exclude_recent, args.family or "")
    if not ranked:
        print("후보가 없다.", file=sys.stderr)
        return 2

    results = []
    for entry in ranked[: max(1, args.top)]:
        tokens, checks = build_tokens(entry["family"], entry["accent"], args.medium)
        results.append({**entry, "tokens": tokens, "checks": checks})
    top = results[0]
    failed = [c for c in top["checks"] if not c["ok"]]

    if args.json:
        print(json.dumps({
            "subject": subject, "medium": args.medium, "mood": args.mood,
            "seed": args.seed or subject,
            "recent": recent_families(),
            "candidates": [{
                "family": r["family"]["name"], "ko": r["family"]["ko"], "score": round(r["score"], 2),
                "accent": r["accent"], "hits": r["hits"], "print_safe": r["family"]["print_safe"],
                "tokens": r["tokens"], "checks": r["checks"],
            } for r in results],
        }, ensure_ascii=False, indent=2))
    else:
        recent = recent_families()
        print(f"[palette] {subject or '(주제 없음)'} · 매체 {args.medium}"
              + (f" · 무드 {args.mood}" if args.mood else ""))
        if recent:
            print(f"  최근 사용 계열: {', '.join(dict.fromkeys(recent))}")
        for n, r in enumerate(results):
            fam = r["family"]
            flag = "  ← 1순위" if n == 0 else ""
            repeat = "  ⚠ 최근에 씀" if fam["name"] in recent else ""
            print(f"\n  [{n + 1}] {fam['name']} ({fam['ko']}) score={r['score']:.1f}{flag}{repeat}")
            print(f"      accent {r['accent']} · 표면 {fam['surfaces'][0]} · 잉크 {fam['ink']}"
                  f" · 인쇄안전 {'o' if fam['print_safe'] else 'x'}")
            if r["hits"]:
                print(f"      맞은 키워드: {', '.join(r['hits'][:8])}")
        print("\n  대비 검사 (1순위):")
        for c in top["checks"]:
            print(f"    {'PASS' if c['ok'] else 'FAIL'}  {c['label']}: {c['ratio']}:1 (≥{c['target']})")
        if repeated := [r for r in results if r["family"]["name"] in recent]:
            print(f"\n  참고: 후보 {', '.join(r['family']['name'] for r in repeated)} 는 최근 사용 계열이다 —"
                  " 다른 표면과 구분해야 하면 --exclude-recent 로 다시 고른다.")

    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(tokens_css(top["family"], top["tokens"], top["accent"], subject, args.medium), encoding="utf-8")
        print(f"\n  wrote {out}")

    if args.record or args.write:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "family": top["family"]["name"], "accent": top["accent"],
                "subject": subject, "medium": args.medium, "mood": args.mood,
            }, ensure_ascii=False) + "\n")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
