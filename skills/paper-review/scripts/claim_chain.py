#!/usr/bin/env python3
"""Claim-to-evidence map and causal-claim audit for a manuscript.

    python3 claim_chain.py paper.md
    python3 claim_chain.py paper.md --design observational --json

Three mechanical checks from the argument-logic pass:
  1. every Abstract/Conclusion claim has a supporting sentence in Results
  2. causal language does not outrun the design
  3. an observational paper discusses at least one alternative explanation

Scores are lexical. A WEAK/UNSUPPORTED verdict is a prompt to read, not a proof.
Exit 0 always (report, not gate); 64 on bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NUM = re.compile(r"\d+(?:[.,]\d+)*")
WORD = re.compile(r"[가-힣]{2,}|[A-Za-z][A-Za-z\-]{2,}")

STOP = {"the", "and", "of", "in", "was", "were", "is", "are", "a", "an", "to", "for", "with",
        "on", "we", "our", "that", "this", "as", "by", "from", "at", "be", "been", "it", "its",
        "these", "those", "than", "then", "also", "but", "or", "not", "no", "have", "has",
        "그리고", "그러나", "또한", "따라서", "이", "그", "것", "수", "등", "및", "위해", "통해",
        "대한", "있는", "없는", "한다", "했다", "이다", "하며", "하여", "에서", "으로", "보다",
        "경우", "때문", "대해", "관련", "따른", "의한", "각", "더", "매우", "본", "있었다", "없었다"}
PARTICLES = ("에서", "에게", "으로", "라고", "부터", "까지", "처럼", "보다", "으로서",
             "은", "는", "이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "만")

RESULT_CUE = re.compile(
    r"상승|증가|감소|낮았|높았|연관|관련이\s*있|예측|독립적|위험(?:을|도|이)|효과가|개선|악화|"
    r"차이를\s*보|유의(?:하게|한)|비율이|"
    r"\b(?:was|were)\s+(?:associated|correlated|related)\b|\bincrease[sd]?\b|\bdecrease[sd]?\b|"
    r"\breduce[sd]?\b|\bimprove[sd]?\b|\bpredict(?:ed|s)?\b|\bindependent(?:ly)?\s+predictor\b|"
    r"\b(?:higher|lower)\b|\bmore likely\b|\bsignificant(?:ly)?\b",
    re.I)

CAUSAL_CUE = re.compile(
    r"인과|유발|초래|때문에|로\s*인해|원인이|야기|"
    r"\b(?:causes?|caused|causing|leads?\s+to|led\s+to|results?\s+in|resulted\s+in|"
    r"due\s+to|because\s+of|drives?|attributable\s+to|"
    r"reduce[sd]?|increase[sd]?|improve[sd]?|prevent(?:s|ed)?)\b",
    re.I)

ALT_CUE = re.compile(
    r"교란|편향|역인과|대안\s*가설|다른\s*설명|제3의\s*변수|잔여|선택\s*편향|생존자|"
    r"\b(?:confound\w*|bias\b|reverse\s+causation|alternative\s+explanation|"
    r"unmeasured|selection\s+bias|survivorship|residual)\b",
    re.I)

DESIGN_CUE = re.compile(
    r"무작위|randomi[sz]ed|\bRCT\b|\bintervention\b|\btrial\b|중재", re.I)


def strip_particle(t: str) -> str:
    for p in PARTICLES:
        if len(t) > len(p) + 1 and t.endswith(p):
            return t[: -len(p)]
    return t


def tokens(text: str) -> set[str]:
    out = set()
    for w in WORD.findall(text):
        w = strip_particle(w.lower())
        if len(w) >= 2 and w not in STOP:
            out.add(w)
    return out


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUM.findall(text)}


def split_sentences(text: str) -> list[tuple[int, str]]:
    out = []
    guarded = re.sub(r"\b(Fig|Figs|vs|e\.g|i\.e|et al|approx|No)\.", r"\1<DOT>", text)
    for lineno, line in enumerate(guarded.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("#", "|", "```", ">", "!")):
            continue
        for part in re.split(r"(?<=[.!?。])\s+", s):
            p = part.replace("<DOT>", ".").strip(" -*")
            if len(p.split()) >= 4 or len(p) >= 20:
                out.append((lineno, p))
    return out


def sections(text: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    cur, buf = "_body", []
    for line in text.splitlines():
        m = re.match(r"^\s{0,3}#{1,4}\s+(.*)$", line)
        if m:
            parts[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip().lower(), []
        else:
            buf.append(line)
    parts[cur] = "\n".join(buf)
    return parts


def find_section(secs: dict[str, str], keys: tuple[str, ...]) -> str:
    return "\n".join(v for k, v in secs.items() if any(t in k for t in keys))


def best_match(claim: str, pool: list[tuple[int, str]]) -> tuple[int | None, float, str, int]:
    ct, cn = tokens(claim), numbers(claim)
    best, best_line, best_text, best_shared = 0.0, None, "", 0
    for lineno, s in pool:
        st = tokens(s)
        if not st or not ct:
            continue
        shared = len(ct & st)
        score = shared / len(ct) + (0.2 if cn and cn & numbers(s) else 0.0)
        if score > best:
            best, best_line, best_text, best_shared = score, lineno, s, shared
    return best_line, round(min(best, 1.0), 2), best_text, best_shared


def main() -> int:
    ap = argparse.ArgumentParser(description="Claim-to-evidence and causal-claim audit.")
    ap.add_argument("manuscript")
    ap.add_argument("--design", default="auto",
                    choices=["auto", "observational", "rct", "qualitative"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-score", type=float, default=0.35)
    a = ap.parse_args()

    path = Path(a.manuscript)
    if not path.exists():
        print(f"missing file: {path}", file=sys.stderr)
        return 64
    text = path.read_text(encoding="utf-8", errors="replace")
    secs = sections(text)

    claim_text = find_section(secs, ("abstract", "초록", "conclusion", "결론"))
    if not claim_text.strip():
        claim_text = text
    evidence_text = find_section(secs, ("results", "결과"))
    evidence = split_sentences(evidence_text) if evidence_text.strip() else split_sentences(text)
    discussion = find_section(secs, ("discussion", "논의", "고찰", "limitation", "한계")) or text

    design = a.design
    if design == "auto":
        design = "rct" if DESIGN_CUE.search(find_section(secs, ("methods", "방법")) or text) \
            else "observational"

    claims = [(ln, s) for ln, s in split_sentences(claim_text) if RESULT_CUE.search(s)]
    findings, rows = [], []
    for ln, claim in claims:
        eline, score, etext, shared = best_match(claim, evidence)
        verdict = ("SUPPORTED" if score >= a.min_score or shared >= 2
                   else ("WEAK" if score >= 0.15 else "UNSUPPORTED"))
        row = {"claim_line": ln, "claim": claim[:180], "verdict": verdict, "score": score,
               "shared_terms": shared, "evidence_line": eline, "evidence": etext[:140]}
        if CAUSAL_CUE.search(claim) and design != "rct":
            row["causal_overreach"] = True
            findings.append({
                "severity": "HIGH", "line": ln,
                "msg": f"인과 어휘({CAUSAL_CUE.search(claim).group(0)}) + 설계={design} — "
                       f"관찰 연구면 associated with / suggests로 내림",
                "quote": claim[:120]})
        if verdict == "UNSUPPORTED":
            findings.append({"severity": "HIGH", "line": ln,
                             "msg": "초록·결론의 결과 주장에 대응하는 Results 문장을 찾지 못함 — "
                                    "근거 문장 추가 또는 주장 삭제",
                             "quote": claim[:120]})
        elif verdict == "WEAK":
            findings.append({"severity": "MED", "line": ln,
                             "msg": f"근거 문장 대응 약함(score {score}) — 수치 근거를 같은 문장에",
                             "quote": claim[:120]})
        rows.append(row)

    if design == "observational" and not ALT_CUE.search(discussion):
        findings.append({"severity": "MED", "line": 0,
                         "msg": "관찰 연구인데 대안 가설·교란·편향 언급이 없음 — "
                                "가장 흔한 심사 지적(제3변수/역인과/선택편향)을 논의에 명시",
                         "quote": ""})

    if a.json:
        print(json.dumps({"file": str(path), "design": design, "claims": rows,
                          "findings": findings}, ensure_ascii=False, indent=2))
        return 0

    print(f"\n## {path}  (design={design})")
    print(f"claims checked={len(rows)} supported="
          f"{sum(1 for r in rows if r['verdict'] == 'SUPPORTED')} "
          f"weak={sum(1 for r in rows if r['verdict'] == 'WEAK')} "
          f"unsupported={sum(1 for r in rows if r['verdict'] == 'UNSUPPORTED')}")
    for r in rows:
        ev = f"L{r['evidence_line']}" if r["evidence_line"] else "—"
        flag = "causal!" if r.get("causal_overreach") else ""
        print(f"  L{r['claim_line']:<4} {r['verdict']:11} {r['score']:.2f} ← {ev:<6} {flag}")
        print(f"        주장: {r['claim'][:110]}")
        if r["evidence"]:
            print(f"        근거: {r['evidence'][:110]}")
    if findings:
        print("\n  지적:")
        for f in findings:
            loc = f"L{f['line']}" if f["line"] else "전체"
            print(f"  [{f['severity']:4}] {loc:<6} {f['msg']}")
    else:
        print("\n  지적 없음 — 어휘 기준. 논증 타당성은 references/argument-logic.md로 직접 확인.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
