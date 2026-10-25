#!/usr/bin/env python3
"""Lexical prose audit for a manuscript section or file.

Reports, with line numbers: AI-writing tells, overclaiming (단정적 어투), number-dump
sentences, over-long sentences, hedge imbalance and repeated sentence-initial connectors.

    python3 prose_lint.py paper.md --lang ko
    python3 prose_lint.py paper.md --json --top 20

Exit codes: 0 always (this is a report, not a gate), 64 on bad usage.
The script counts; it does not judge. Read every flagged line before reporting it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# (id, label, severity, pattern, why)
TELLS = [
    ("ai01", "significance inflation", "HIGH",
     r"(?:매우|대단히|극히)\s*(?:중요|유의|의미)|중요한\s*(?:역할|의의)를\s*하다|"
     r"\b(?:very|extremely)\s+(?:important|significant|useful|valuable)\b|"
     r"\bplays?\s+an?\s+\w*\s*role\b|"
     r"\b(?:pivotal|paramount|groundbreaking|game-?changing|delve[sd]?|tapestry|realm)\b",
     "가치를 주장하는 형용사가 근거 없이 붙음 — 지우고 사실로 대체"),
    ("ai02", "hollow summation", "MED",
     r"이를\s*통해|이와\s*같이|이상의\s*결과(?:로|는)|이는\s*곧|결론적으로\s*말해|"
     r"\b(?:it is worth noting|it is important to note|in conclusion, it)\b",
     "앞 문장을 다시 말하는 접속구 — 대개 통째로 삭제 가능"),
    ("ai03", "empty filler", "MED",
     r"(?:매우|다양한|다채로운|폭넓은|주요한|핵심적인)\s*(?:연구|결과|방법|요소|접근)|"
     r"\b(?:various|numerous|a wide range of|robust|seamless)\b",
     "내용 없는 수식어 — 수치나 범위로 바꾸거나 삭제"),
    ("ai04", "formulaic contrast", "LOW",
     r"단순히\s*.{0,20}(?:아니라|뿐만\s*아니라)|not only\s+.{0,30}\bbut also\b|"
     r"\b(?:moreover|furthermore|additionally)\b\s*,",
     "대조·첨가 공식 — 한 문단에 두 번 이상이면 AI 문체로 읽힘"),
    ("ai05", "tricolon padding", "LOW",
     r"\S+,\s*\S+,\s*(?:그리고|및)\s*\S+(?:를|을)\s*(?:제공|보여|시사)",
     "3항 나열로 문장을 부풀림 — 실제로 필요한 항목만 남김"),
    ("ai06", "meta narration", "HIGH",
     r"본\s*(?:연구|논문)에서는\s*.{0,15}(?:살펴보고자|알아보고자|다루고자)|"
     r"\bthis (?:study|paper) (?:aims to|seeks to|endeavors to)\b",
     "독자에게 할 말을 예고하는 메타 문장 — 서론 1회 외에는 삭제"),
]

OVERCLAIM = [
    ("oc01", "causal overclaim", "HIGH",
     r"입증(?:되었|했다|한다)|증명(?:되었|했다|한다)|인과\s*관계를\s*(?:확인|입증)|"
     r"\b(?:proves?|proved|demonstrates? conclusively|establishes? causality)\b",
     "관찰 연구가 인과를 주장 — associated with / suggests 로 내림"),
    ("oc02", "certainty adverb", "MED",
     r"명백히|분명히|확실히|틀림없이|반드시|절대(?:로)?|"
     r"\b(?:clearly|obviously|undoubtedly|certainly|definitively)\b",
     "확신 부사 — 근거 강도와 무관하게 단정"),
    ("oc03", "novelty inflation", "MED",
     r"최초로|유일하게|전례\s*없는|세계\s*최초|국내\s*최초|"
     r"\b(?:the first ever|unprecedented|unique(?:ly)? the only)\b",
     "최초·유일 주장 — 선행연구 확인 근거가 같은 문장에 있어야 함"),
    ("oc04", "universal quantifier", "MED",
     r"모든\s*(?:환자|경우|대상)|항상|전혀\s*없|"
     r"\b(?:all patients|always|never|invariably)\b",
     "전칭 양화 — 표본이 뒷받침하지 않으면 한정어 필요"),
]

HEDGES = re.compile(
    r"시사(?:한다|할\s*수\s*있다)|가능성이\s*있다|생각된다|보인다|경향이\s*있다|"
    r"associated\s+with|may\s+be|might\s+be|suggests?|appears?\s+to|is\s+consistent\s+with",
    re.I,
)

CONNECTORS = re.compile(
    r"^\s*(?:또한|따라서|그러나|하지만|한편|즉|그러므로|나아가|더욱이|"
    r"However|Moreover|Furthermore|Therefore|Thus|Additionally|In addition)\b[,，]?",
    re.M,
)

NUM = re.compile(
    r"p\s*[<=>]\s*0?\.\d+|\b95\s*%\s*(?:CI|confidence)|"
    r"(?<![\w.])[-−]?\d+(?:[.,]\d+)*(?:\s*(?:%|mg|kg|mL|L|mm|cm|Gy|mmol|mmHg|"
    r"years?|months?|days?|세|명|개|건|배))?"
)

STOP = {"the", "and", "of", "in", "was", "were", "a", "an", "to", "for", "with", "on"}


def sentences(text: str) -> list[tuple[int, str]]:
    """Split into (1-based line number, sentence). Line = where the sentence starts."""
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "```", ">", "!", "%")):
            continue
        # protect common abbreviations so "Fig. 1" does not become a sentence end
        guarded = re.sub(r"\b(Fig|Figs|vs|e\.g|i\.e|et al|approx|No)\.", r"\1<DOT>", stripped)
        for part in re.split(r"(?<=[.!?。])\s+", guarded):
            s = part.replace("<DOT>", ".").strip()
            if len(s) > 0:
                out.append((lineno, s))
    return out


def word_count(s: str) -> int:
    return len([w for w in re.split(r"\s+", s) if w])


def count_numeric(s: str) -> int:
    return len(NUM.findall(s))


def scan(text: str) -> dict:
    findings: list[dict] = []
    for pid, label, sev, pat, why in TELLS + OVERCLAIM:
        rx = re.compile(pat, re.I)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in rx.finditer(line):
                findings.append({"id": pid, "label": label, "severity": sev,
                                 "line": lineno, "match": m.group(0)[:60], "why": why})

    sents = sentences(text)
    numbers = 0
    long_sents = 0
    hedges = 0
    for lineno, s in sents:
        n = count_numeric(s)
        numbers += n
        if n >= 4:
            findings.append({"id": "num-dump", "label": "number-dump sentence", "severity": "MED",
                             "line": lineno, "match": s[:90],
                             "why": f"한 문장에 수치 {n}개 — 해석 문장을 붙이고 나머지는 표로"})
        wc = word_count(s)
        if (wc > 45) or (len(s) > 170 and wc <= 45):
            long_sents += 1
            findings.append({"id": "long", "label": "over-long sentence", "severity": "LOW",
                             "line": lineno, "match": s[:90],
                             "why": f"{len(s)}자 / {wc}단어 — 두 문장으로 분리"})
        if HEDGES.search(s):
            hedges += 1

    conn: dict[str, list[int]] = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        m = CONNECTORS.match(line)
        if m:
            key = m.group(0).strip(" ,，")
            conn.setdefault(key, []).append(lineno)
    for key, lines in conn.items():
        if len(lines) >= 3:
            findings.append({"id": "connector", "label": "repeated connector", "severity": "LOW",
                             "line": lines[0], "match": f"{key} ×{len(lines)}",
                             "why": f"문단 첫머리 접속어 반복 (L{', '.join(map(str, lines[:8]))})"})

    by_sev = {"HIGH": 0, "MED": 0, "LOW": 0}
    for f in findings:
        by_sev[f["severity"]] += 1
    total_words = len(text.split())
    return {
        "words": total_words,
        "sentences": len(sents),
        "numeric_tokens": numbers,
        "hedged_sentences": hedges,
        "long_sentences": long_sents,
        "counts": by_sev,
        "density_per_1000": round(len([f for f in findings if f["id"].startswith(("ai", "oc"))])
                                  / max(total_words, 1) * 1000, 2),
        "findings": findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Lexical prose audit for a manuscript.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=40, help="max findings printed")
    ap.add_argument("--lang", default="ko", choices=["ko", "en"], help="affects the header language")
    a = ap.parse_args()

    reports = []
    for p in a.files:
        path = Path(p)
        if not path.exists():
            print(f"missing file: {path}", file=sys.stderr)
            return 64
        r = scan(path.read_text(encoding="utf-8", errors="replace"))
        r["file"] = str(path)
        reports.append(r)

    if a.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    for r in reports:
        c = r["counts"]
        print(f"\n## {r['file']}")
        print(f"words={r['words']} sentences={r['sentences']} numeric_tokens={r['numeric_tokens']} "
              f"hedged={r['hedged_sentences']} long={r['long_sentences']}")
        print(f"AI-tell + overclaim density: {r['density_per_1000']} per 1000 words "
              f"(target < 2.0) | HIGH={c['HIGH']} MED={c['MED']} LOW={c['LOW']}")
        if r["hedged_sentences"] and r["sentences"]:
            ratio = r["hedged_sentences"] / r["sentences"]
            if ratio > 0.45:
                print(f"! hedge 비율 {ratio:.0%} — 과잉 hedge 의심: 핵심 결과가 무력해짐")
            elif ratio < 0.05 and r["sentences"] > 20:
                print(f"! hedge 비율 {ratio:.0%} — 단정 위험: 관찰 연구라면 완화 표현 필요")
        shown = r["findings"][: a.top]
        for f in shown:
            print(f"  [{f['severity']:4}] L{f['line']:<5} {f['label']:24} «{f['match']}»")
            print(f"         → {f['why']}")
        if len(r["findings"]) > len(shown):
            print(f"  … {len(r['findings']) - len(shown)} more (use --json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
