#!/usr/bin/env python3
"""check_cuecards.py — verify a cue-card PDF really is printable and complete.

Checks (all from the PDF itself, no re-rendering):
  * every page is A4 portrait
  * each page carries 2 cards (the last page may carry 1) and each half is non-empty
  * the card labels read "카드 NN / TT" and NN runs 01..TT with one consistent TT
  * optional --source: every script block still appears in the printed text, which is
    what catches a block clipped by a card that was too full

    python3 check_cuecards.py out.pdf [--source script.md] [--per-page 2|4]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_cuecards as mc  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--source", help="script the PDF was made from (fidelity check)")
    parser.add_argument("--part", action="append", default=[],
                        help="part filter used when the PDF was made (mirrors make_cuecards.py)")
    parser.add_argument("--skip-front", action="store_true", help="front-matter filter used at build time")
    parser.add_argument("--per-page", type=int, choices=(2, 4), default=2)
    args = parser.parse_args()

    try:
        import pypdf
    except ImportError:
        print("pypdf is required: python -m pip install pypdf", file=sys.stderr)
        return 2

    pdf = Path(args.pdf).expanduser()
    if not pdf.is_file():
        print(f"not found: {pdf}", file=sys.stderr)
        return 2

    reader = pypdf.PdfReader(str(pdf))
    texts = [page.extract_text() or "" for page in reader.pages]
    problems: list[str] = []

    for number, page in enumerate(reader.pages, 1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if not (560 < width < 620 and 800 < height < 880):
            problems.append(f"p{number}: {width:.0f}x{height:.0f} pt is not A4 portrait")

    labels = re.findall(r"카드\s*(\d+)\s*/\s*(\d+)", " ".join(texts))
    if not labels:
        problems.append("no '카드 NN / TT' label found — is this a cue-card PDF?")
    totals = {total for _, total in labels}
    if len(totals) > 1:
        problems.append(f"inconsistent card totals: {sorted(totals)}")
    numbers = [int(number) for number, _ in labels]
    if numbers != list(range(1, len(numbers) + 1)):
        problems.append(f"card numbering is not 01..{len(numbers)}: {numbers[:12]}…")

    per_page = args.per_page
    expected_pages = (len(numbers) + per_page - 1) // per_page if numbers else 0
    if expected_pages and len(reader.pages) != expected_pages:
        problems.append(f"{len(reader.pages)} pages for {len(numbers)} cards "
                        f"(expected {expected_pages} at {per_page}/page)")
    for number, text in enumerate(texts, 1):
        found = len(re.findall(r"카드\s*\d+\s*/\s*\d+", text))
        if found == 0:
            problems.append(f"p{number}: no card header (blank or mis-paginated page)")
        elif found < per_page and number != len(texts):
            problems.append(f"p{number}: only {found} card(s) on a non-final page")

    missing: list[str] = []
    if args.source:
        source = Path(args.source).expanduser()
        if not source.is_file():
            problems.append(f"source not found: {source}")
        else:
            blocks = mc.select_blocks(mc.read_script(source, 200, False), args.part, args.skip_front)
            flat = mc.normalize(" ".join(texts))
            for block in blocks:
                if block.kind in ("part", "section", "rule", "tcap"):
                    continue
                probe = (mc.normalize(block.attrs.get("key", "")) + mc.normalize(block.attrs.get("val", ""))
                         if block.kind == "trow" else mc.normalize(block.text))
                if len(probe) < 8:
                    continue
                probes = [probe[:24]] + ([probe[-24:]] if len(probe) >= 40 else [])
                if any(p not in flat for p in probes):
                    missing.append((block.text or block.attrs.get("key", ""))[:60])
            if missing:
                problems.append(f"{len(missing)} script block(s) missing from the PDF, "
                                f"e.g. {missing[0]!r}")

    cards = len(numbers)
    print(f"{pdf.name}: {len(reader.pages)} A4 pages, {cards} cards"
          + (f" (source: {Path(args.source).name})" if args.source else ""))
    for problem in problems:
        print(f"  FAIL {problem}")
    if problems:
        return 1
    print("  PASS geometry, card numbering, page fill"
          + (", source text complete" if args.source else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
