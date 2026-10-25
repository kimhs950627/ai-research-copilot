#!/usr/bin/env python3
"""Check whether a presentation deck carries the paper's core claims.

    python3 deck_coverage.py --manuscript paper.md --deck deck.md
    python3 deck_coverage.py --manuscript paper.md --deck deck.md --json --min-score 0.45

Claims are taken from the Abstract and Conclusion when those headings exist, otherwise from
sentences that carry a number. Each claim is matched against every slide; coverage is keyword
overlap plus a bonus when the claim's numbers appear on the slide.

Scores are indicative — Korean tokenisation here is whitespace + particle stripping, not a
morphological analyser. Confirm every "missing" by reading the deck. Exit 0 always.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STOP_KO = {"그리고", "그러나", "또한", "따라서", "이", "그", "저", "것", "수", "등", "및", "위해",
           "통해", "대한", "있는", "없는", "한다", "했다", "이다", "하며", "하여", "에서", "으로",
           "보다", "경우", "때문", "대해", "관련", "따른", "의한", "각", "더", "매우", "본"}
STOP_EN = {"the", "and", "of", "in", "was", "were", "is", "are", "a", "an", "to", "for", "with",
           "on", "we", "our", "that", "this", "as", "by", "from", "at", "be", "been", "it", "its",
           "these", "those", "than", "then", "also", "but", "or", "not", "no", "have", "has"}

PARTICLES = ("에서", "에게", "으로", "라고", "부터", "까지", "처럼", "보다", "으로서",
             "은", "는", "이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "만")

NUM = re.compile(r"\d+(?:[.,]\d+)*")
WORD = re.compile(r"[가-힣]{2,}|[A-Za-z][A-Za-z\-]{2,}")


def strip_particle(tok: str) -> str:
    for p in PARTICLES:
        if len(tok) > len(p) + 1 and tok.endswith(p):
            return tok[: -len(p)]
    return tok


def tokens(text: str) -> set[str]:
    out: set[str] = set()
    for w in WORD.findall(text):
        w = strip_particle(w.lower())
        if len(w) < 2 or w in STOP_KO or w in STOP_EN:
            continue
        out.add(w)
    return out


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUM.findall(text)}


def sections(text: str) -> dict[str, str]:
    """Split on markdown headings; keys are lowercased heading text."""
    parts: dict[str, str] = {}
    current = "_body"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s{0,3}#{1,4}\s+(.*)$", line)
        if m:
            parts[current] = "\n".join(buf)
            current = m.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    parts[current] = "\n".join(buf)
    return parts


def claim_sentences(text: str) -> list[str]:
    out = []
    guarded = re.sub(r"\b(Fig|Figs|vs|e\.g|i\.e|et al|approx|No)\.", r"\1<DOT>", text)
    for part in re.split(r"(?<=[.!?。])\s+", guarded):
        s = part.replace("<DOT>", ".").strip(" -*\n\t")
        if len(s.split()) >= 5 or len(s) >= 15:
            out.append(s)
    return out


def pick_claims(manuscript: str, limit: int) -> list[tuple[str, str]]:
    secs = sections(manuscript)
    key = [k for k in secs if any(t in k for t in ("abstract", "초록", "conclusion", "결론"))]
    claims: list[tuple[str, str]] = []
    for k in key:
        for s in claim_sentences(secs[k]):
            claims.append(("key", s))
    if not claims:
        for s in claim_sentences(manuscript):
            if numbers(s):
                claims.append(("numeric", s))
    seen: set[str] = set()
    uniq = []
    for kind, s in claims:
        norm = s[:80]
        if norm in seen:
            continue
        seen.add(norm)
        uniq.append((kind, s))
    return uniq[:limit]


def split_slides(deck: str) -> list[tuple[str, str]]:
    chunks = re.split(r"(?m)^\s*(?:---+|#{1,3}\s+.+|Slide\s+\d+.*)$", deck)
    out = []
    for i, c in enumerate(chunks):
        t = c.strip()
        if t:
            out.append((f"S{i + 1}", t))
    if len(out) <= 1:  # no separators: split on blank-line groups
        paras = [p.strip() for p in re.split(r"\n\s*\n", deck) if p.strip()]
        out = [(f"S{i + 1}", p) for i, p in enumerate(paras)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Deck content coverage vs manuscript.")
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-score", type=float, default=0.4,
                    help="keyword overlap at or above this counts as covered")
    ap.add_argument("--claims", type=int, default=30, help="max claims to check")
    a = ap.parse_args()

    mp, dp = Path(a.manuscript), Path(a.deck)
    for p in (mp, dp):
        if not p.exists():
            print(f"missing file: {p}", file=sys.stderr)
            return 64
    ms = mp.read_text(encoding="utf-8", errors="replace")
    dk = dp.read_text(encoding="utf-8", errors="replace")

    claims = pick_claims(ms, a.claims)
    slides = split_slides(dk)
    slide_tokens = {sid: tokens(t) for sid, t in slides}
    slide_numbers = {sid: numbers(t) for sid, t in slides}
    all_slide_nums = set().union(*slide_numbers.values()) if slide_numbers else set()

    rows = []
    for kind, claim in claims:
        ct = tokens(claim)
        cn = numbers(claim)
        if not ct:
            continue
        best_sid, best = "", 0.0
        for sid, st in slide_tokens.items():
            if not st:
                continue
            overlap = len(ct & st) / len(ct)
            q = overlap + (0.15 if cn and cn <= slide_numbers[sid] else 0.0)
            if q > best:
                best_sid, best = sid, q
        num_hit = (cn <= all_slide_nums) if cn else True
        rows.append({
            "claim": claim[:160], "kind": kind,
            "score": round(min(best, 1.0), 2), "best_slide": best_sid,
            "numbers": sorted(cn), "numbers_missing": sorted(cn - all_slide_nums),
            "numbers_present": num_hit,
            "covered": best >= a.min_score and num_hit,
        })

    missing = [r for r in rows if not r["covered"]]
    result = {"manuscript": str(mp), "deck": str(dp), "slides": len(slides),
              "claims": len(rows), "covered": len(rows) - len(missing), "missing": len(missing),
              "rows": rows}
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"\n## {dp} vs {mp}")
    print(f"slides={len(slides)} claims={len(rows)} covered={result['covered']} "
          f"missing={len(missing)}")
    for r in rows:
        mark = "OK " if r["covered"] else "MISS"
        numflag = "" if r["numbers_present"] else f" [숫자 누락 {r['numbers_missing']}]"
        print(f"  [{mark}] {r['score']:.2f} {r['best_slide'] or '-':>3}{numflag}  {r['claim'][:100]}")
    if missing:
        print(f"\n덱이 담지 않은 핵심 주장 {len(missing)}건 — 위 MISS 행을 슬라이드 단위로 확인.")
    else:
        print("\n모든 핵심 주장이 덱에 등장 — 덱이 논문을 그대로 옮긴 형태일 수 있으니 "
              "선별(selection)을 별도로 본다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
