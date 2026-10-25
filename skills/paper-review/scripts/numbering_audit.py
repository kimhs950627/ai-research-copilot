#!/usr/bin/env python3
"""Audit table / figure / reference numbering and in-text citation placement.

    python3 numbering_audit.py paper.md --captions-dir tables/ --captions-dir figures/
    python3 numbering_audit.py paper.md --json

Catches: item defined but never cited, cited but never defined, duplicates, gaps,
and out-of-order first citation. Exit 1 when a HIGH finding exists, 0 when clean.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TABLE_CITE = re.compile(r"(?<![\w-])(?:Table|TABLE|표)\s*(S?\d+[A-Za-z]?)")
FIG_CITE = re.compile(r"(?<![\w-])(?:Figure|FIGURE|Fig\.?|그림)\s*(S?\d+[A-Za-z]?)")
BRACKET = re.compile(r"\[(\d+(?:\s*[,\-–]\s*\d+)*)\]")
CAPTION = re.compile(
    r"^\s*(?:\*\*)?\[?(?:Table|TABLE|표|Figure|FIGURE|Fig\.?|그림)\s*(S?\d+[A-Za-z]?)\]?"
    r"(?:\*\*)?\s*[.:|)\]—-]",
)


def read_files(paths: list[str]) -> list[tuple[str, str]]:
    out = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        out.append((str(path), path.read_text(encoding="utf-8", errors="replace")))
    return out


def expand(nums: str) -> list[int]:
    vals: list[int] = []
    for part in re.split(r"\s*,\s*", nums):
        if re.search(r"[–-]", part):
            lo, hi = re.split(r"\s*[–-]\s*", part)
            try:
                vals.extend(range(int(lo), int(hi) + 1))
            except ValueError:
                pass
        elif part.isdigit():
            vals.append(int(part))
    return vals


def audit(main: tuple[str, str], caption_files: list[tuple[str, str]]) -> dict:
    fname, text = main
    findings: list[dict] = []
    citations: list[dict] = []
    defined: dict[str, list[str]] = {}

    for kind, rx in (("table", TABLE_CITE), ("figure", FIG_CITE)):
        for lineno, line in enumerate(text.splitlines(), 1):
            if CAPTION.match(line):
                continue  # a caption, not a citation
            for m in rx.finditer(line):
                citations.append({"kind": kind, "num": m.group(1), "line": lineno, "file": fname})
            cm = CAPTION.match(line)
            if cm:
                defined.setdefault(kind, []).append(cm.group(1))

    for cname, ctext in caption_files:
        for lineno, line in enumerate(ctext.splitlines(), 1):
            low = line.strip().lower()
            if low.startswith(("|", "#")) and "table" not in low and "figure" not in low:
                continue
            cm = CAPTION.match(line)
            if cm:
                kind = "table" if re.match(r"\s*(?:\*\*)?\[?(?:Table|TABLE|표)", line) else "figure"
                defined.setdefault(kind, []).append(cm.group(1))
            elif low.startswith("|") and re.match(r"\|\s*S?\d+", low):
                num = re.match(r"\|\s*(S?\d+)", low).group(1)
                defined.setdefault("table", []).append(num)

    for kind in ("table", "figure"):
        cites = [c for c in citations if c["kind"] == kind]
        cited_nums = {c["num"] for c in cites}
        defs = defined.get(kind, [])
        def_nums = set(defs)

        for num in sorted(def_nums - cited_nums):
            findings.append({"severity": "HIGH", "kind": kind, "num": num,
                             "msg": f"{kind} {num} 이(가) 정의되었으나 본문에서 인용되지 않음"})
        for num in sorted(cited_nums - def_nums):
            findings.append({"severity": "HIGH", "kind": kind, "num": num,
                             "msg": f"{kind} {num} 이(가) 본문에서 인용되었으나 정의(캡션)가 없음"})
        for num in sorted({n for n in defs if defs.count(n) > 1}):
            findings.append({"severity": "MED", "kind": kind, "num": num,
                             "msg": f"{kind} {num} 캡션이 중복 정의됨 ×{defs.count(num)}"})

        main_nums = sorted(int(n) for n in def_nums if n.isdigit())
        if main_nums:
            missing = [n for n in range(1, max(main_nums) + 1) if n not in main_nums]
            if missing:
                findings.append({"severity": "MED", "kind": kind, "num": ",".join(map(str, missing)),
                                 "msg": f"{kind} 번호 결번: {missing}"})

        first: dict[str, int] = {}
        for c in cites:
            first.setdefault(c["num"], c["line"])
        order = [n for n in first if n.isdigit()]
        for i in range(1, len(order)):
            if int(order[i]) < int(order[i - 1]):
                findings.append({"severity": "MED", "kind": kind, "num": order[i],
                                 "line": first[order[i]],
                                 "msg": f"{kind} {order[i]} 이(가) {kind} {order[i-1]} 보다 먼저 인용됨 "
                                        f"(L{first[order[i]]} < L{first[order[i-1]]})"})

    refs: set[int] = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in BRACKET.finditer(line):
            for n in expand(m.group(1)):
                if n not in refs:
                    refs.add(n)
                    citations.append({"kind": "ref", "num": str(n), "line": lineno, "file": fname})
    if refs:
        missing = [n for n in range(1, max(refs) + 1) if n not in refs]
        if missing:
            findings.append({"severity": "MED", "kind": "ref", "num": ",".join(map(str, missing)),
                             "msg": f"참고문헌 번호 결번: {missing}"})
        seq = [c["num"] for c in citations if c["kind"] == "ref"]
        first_ref: dict[str, int] = {}
        for c in citations:
            if c["kind"] == "ref":
                first_ref.setdefault(c["num"], c["line"])
        ordr = sorted(first_ref, key=lambda k: first_ref[k])
        breaks = [n for i, n in enumerate(ordr) if i and int(n) < int(ordr[i - 1])]
        if breaks:
            findings.append({"severity": "MED", "kind": "ref", "num": ",".join(breaks[:6]),
                             "msg": f"참고문헌 번호가 첫 인용 순서와 불일치 (예: {breaks[:6]})"})
        del seq

    seq_kinds = {"table": sorted({c["num"] for c in citations if c["kind"] == "table"}),
                 "figure": sorted({c["num"] for c in citations if c["kind"] == "figure"}),
                 "counts": {}}
    for kind in ("table", "figure", "ref"):
        seq_kinds["counts"][kind] = len({c["num"] for c in citations if c["kind"] == kind})
    return {"file": fname, "findings": findings, "summary": seq_kinds,
            "citation_total": len(citations)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit numbering and citation placement.")
    ap.add_argument("manuscript")
    ap.add_argument("--captions-dir", action="append", default=[],
                    help="directory or file holding the table/figure collection (repeatable)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    main_path = Path(a.manuscript)
    if not main_path.exists():
        print(f"missing file: {main_path}", file=sys.stderr)
        return 64
    cap_files: list[tuple[str, str]] = []
    for d in a.captions_dir:
        p = Path(d)
        if p.is_dir():
            cap_files += read_files(sorted(str(f) for f in p.iterdir()
                                           if f.suffix.lower() in {".md", ".txt", ".csv"}))
        else:
            cap_files += read_files([str(p)])
    if not cap_files:
        print("! no --captions-dir given: only in-text numbering is checked", file=sys.stderr)

    r = audit((str(main_path), main_path.read_text(encoding="utf-8", errors="replace")), cap_files)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        c = r["summary"]["counts"]
        print(f"\n## {r['file']}")
        print(f"citations: table={c['table']} figure={c['figure']} ref={c['ref']} "
              f"(total mentions {r['citation_total']})")
        if not r["findings"]:
            print("PASS — 정의·인용 1:1, 번호 순서 정상")
        for f in r["findings"]:
            loc = f" L{f['line']}" if "line" in f else ""
            print(f"  [{f['severity']:4}] {f['kind']} {f['num']}{loc} — {f['msg']}")
    return 1 if any(f["severity"] == "HIGH" for f in r["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
