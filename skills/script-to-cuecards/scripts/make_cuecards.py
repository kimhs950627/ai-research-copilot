#!/usr/bin/env python3
"""make_cuecards.py — turn a speaking script into printable speaker cue cards (A4 PDF).

    script (.md/.txt/.docx)  ->  blocks  ->  print HTML  ->  headless Chrome  ->  PDF

One portrait A4 sheet carries two 148.4 mm cards, split by a dashed cut line. Cards are
filled by measuring the real rendered height inside the page (assets/paginate.js), so
nothing is shrunk and nothing is dropped; text that does not fit continues on the next
card. No third-party Python package is required — `pypdf`, when present, is used to drop
trailing blank pages and to run the geometry/text self-check.

Card units come from the script itself:
  #  part             deck title / 참고 자료 section
  ## N. 제목 — 45초    one card, with §number and timing badge
  ### 부제목           bold sub-heading inside a card
  - 불릿  | 표 |  > 무대: 지시  |  [청중 보기]  |  ---
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

WIN_CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
LINUX_CHROME = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                "microsoft-edge", "msedge")
DEFAULT_WIN_TMP = "/mnt/c/Users/pc/AppData/Local/Temp"


# ------------------------------------------------------------------------ parsing

class Block:
    """One scannable unit on a card: a paragraph, a bullet, a direction, a table row."""

    __slots__ = ("kind", "text", "title", "num", "time", "attrs")

    def __init__(self, kind, text="", title="", num="", time="", attrs=None):
        self.kind, self.text, self.title = kind, text, title
        self.num, self.time = num, time
        self.attrs = attrs or {}


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise SystemExit(f"cannot decode {path.name}; save it as UTF-8")


def split_heading(raw: str):
    """'6. SupCon은 임베딩의 모양을 바꾼다 — 60초' -> ('6', 'SupCon은 …', '60초')"""
    title, num, timing = raw.strip(), "", ""
    match = re.match(r"^(\d+)\s*[.)]\s+(.*)$", title)
    if match:
        num, title = match.group(1), match.group(2)
    match = re.search(r"[\s—–\-]+\(?(\d+\s*(?:초|분)|[\d:]+\s*분?)\)?\s*$", title)
    if match:
        timing = match.group(1).strip()
        title = title[: match.start()].strip()
    return num, title.rstrip(" —–-·"), timing


def sentence_blocks(text: str, limit: int) -> list[str]:
    """Group sentences so that no block exceeds `limit` characters (keeps blocks splittable)."""
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    out: list[str] = []
    buffer = ""
    for part in parts:
        if buffer and len(buffer) + 1 + len(part) > limit:
            out.append(buffer)
            buffer = part
        else:
            buffer = f"{buffer} {part}".strip()
    if buffer:
        out.append(buffer)
    return out or [text.strip()]


STRUCTURAL = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```|~~~|---|\*\*\*|___|\[[^\[\]]*\]\s*$)")


def parse_markdown(text: str, block_chars: int, keep_breaks: bool) -> list[Block]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n---\n").split("\n")
    blocks: list[Block] = []
    index, fence = 0, False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            index += 1
            continue
        if fence:
            blocks.append(Block("code", line))
            index += 1
            continue
        if not stripped:
            index += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            blocks.append(Block("rule"))
            index += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            raw = stripped[level:].strip()
            if level == 1:
                blocks.append(Block("part", title=re.sub(r"\s*\(.*?\)\s*$", "", raw).strip()))
            elif level == 2:
                num, title, timing = split_heading(raw)
                blocks.append(Block("section", title=title, num=num, time=timing))
            else:
                blocks.append(Block("sub", raw))
            index += 1
            continue

        if stripped.startswith(">"):
            quote: list[str] = []
            while index < len(lines) and (lines[index].strip().startswith(">") or not lines[index].strip()):
                if not lines[index].strip():
                    if index + 1 < len(lines) and lines[index + 1].strip().startswith(">"):
                        quote.append("")
                        index += 1
                        continue
                    break
                quote.append(re.sub(r"^\s*>\s?", "", lines[index]).strip())
                index += 1
            groups: list[str] = []
            buffer: list[str] = []
            for part in quote:
                if part:
                    buffer.append(part)
                elif buffer:
                    groups.append(" ".join(buffer))
                    buffer = []
            if buffer:
                groups.append(" ".join(buffer))
            for group in groups:
                for chunk in sentence_blocks(group, block_chars):
                    kind = "dir" if re.match(r"^\s*(무대|※)\s*[:：]", chunk) else "quote"
                    blocks.append(Block(kind, chunk))
            continue

        if stripped.startswith("|"):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            if rows:
                blocks.append(Block("tcap", " · ".join(cell for cell in rows[0] if cell)))
                for row in rows[1:]:
                    blocks.append(Block("trow", attrs={
                        "key": row[0] if row else "",
                        "val": " · ".join(cell for cell in row[1:] if cell)}))
            continue

        if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            while index < len(lines):
                item = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[index])
                if not item:
                    break
                marker = "•" if item.group(2) in "-*+" else re.match(r"\d+", item.group(2)).group(0) + "."
                body = item.group(3).strip()
                index += 1
                while (index < len(lines) and lines[index].strip()
                       and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[index])
                       and not STRUCTURAL.match(lines[index])):
                    body += " " + lines[index].strip()
                    index += 1
                for chunk in sentence_blocks(body, block_chars):
                    blocks.append(Block("li", chunk, attrs={"marker": marker}))
            continue

        buffer = []
        while (index < len(lines) and lines[index].strip()
               and not STRUCTURAL.match(lines[index])):
            buffer.append(lines[index])
            index += 1
        if not buffer:  # a lone bracket cue line such as [청중 보기]
            buffer = [lines[index]]
            index += 1
        joined = "\n".join(buffer) if keep_breaks else " ".join(part.strip() for part in buffer)
        for chunk in sentence_blocks(joined, block_chars):
            blocks.append(Block("p", chunk))

    return blocks


def parse_docx(path: Path, block_chars: int) -> list[Block]:
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.text.paragraph import Paragraph as DocParagraph
        from docx.table import Table
    except ImportError:
        raise SystemExit("DOCX needs python-docx: python -m pip install python-docx")

    document = Document(str(path))
    blocks: list[Block] = []
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph = DocParagraph(child, document)
            text = paragraph.text.strip()
            if not text:
                continue
            style = paragraph.style.name if paragraph.style else ""
            if text in ("---", "<!-- card -->", r"\pagebreak"):
                blocks.append(Block("rule"))
            elif re.search(r"Heading\s*1", style):
                blocks.append(Block("part", title=text))
            elif re.search(r"Heading\s*2", style):
                num, title, timing = split_heading(text)
                blocks.append(Block("section", title=title, num=num, time=timing))
            elif re.search(r"Heading\s*\d", style):
                blocks.append(Block("sub", text))
            elif re.match(r"^무대\s*[:：]", text):
                blocks.append(Block("dir", text))
            else:
                for chunk in sentence_blocks(text, block_chars):
                    blocks.append(Block("p", chunk))
        elif child.tag == qn("w:tbl"):
            for row in Table(child, document).rows:
                cells = [cell.text.strip() for cell in row.cells]
                blocks.append(Block("trow", attrs={
                    "key": cells[0] if cells else "",
                    "val": " · ".join(cell for cell in cells[1:] if cell)}))
    return blocks


def select_blocks(blocks: list[Block], parts: list[str], skip_front: bool) -> list[Block]:
    """--part keeps only matching H1 parts; --skip-front drops the cover/metadata head
    (the part heading itself is kept, so the card footer still says which deck it is)."""
    if parts:
        kept: list[Block] = []
        active = False
        for block in blocks:
            if block.kind == "part":
                active = any(part.lower() in block.title.lower() for part in parts)
            if active:
                kept.append(block)
        blocks = kept
    if skip_front:
        kept, started = [], False
        for block in blocks:
            if block.kind == "section":
                started = True
            if started or block.kind == "part":
                kept.append(block)
        blocks = kept
    return blocks


def read_script(path: Path, block_chars: int, keep_breaks: bool) -> list[Block]:
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown", ".txt"):
        return parse_markdown(read_text(path), block_chars, keep_breaks and suffix != ".txt")
    if suffix == ".docx":
        return parse_docx(path, block_chars)
    raise SystemExit(f"unsupported extension {suffix}: use .md, .markdown, .txt or .docx")


# ---------------------------------------------------------------------- html output

LINK = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)\)")
CHIP = re.compile(r"\[([^\[\]]{1,40})\]")


def inline(text: str) -> str:
    out = html.escape(text)
    out = LINK.sub(lambda m: f"{m.group(1)} ({m.group(2)})", out)
    out = CHIP.sub(r'<span class="chip">\1</span>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def blocks_to_html(blocks: list[Block]) -> str:
    out: list[str] = []
    for block in blocks:
        if block.kind == "part":
            out.append(f'<div class="b-part" data-kind="part" data-title="{html.escape(block.title)}"></div>')
        elif block.kind == "section":
            out.append('<div class="b-section" data-kind="section" '
                       f'data-title="{html.escape(block.title)}" data-num="{html.escape(block.num)}" '
                       f'data-time="{html.escape(block.time)}"></div>')
        elif block.kind == "rule":
            out.append('<div class="b-rule" data-kind="rule"></div>')
        elif block.kind == "sub":
            out.append(f'<div class="b-sub" data-kind="sub">{inline(block.text)}</div>')
        elif block.kind == "li":
            marker = html.escape(block.attrs.get("marker", "•"))
            out.append(f'<div class="b-li" data-kind="li"><span class="mk">{marker}</span>'
                       f'{inline(block.text)}</div>')
        elif block.kind == "dir":
            label = "무대" if re.match(r"^\s*무대", block.text) else "지시"
            body = inline(re.sub(r"^\s*(무대|※)\s*[:：]\s*", "", block.text))
            out.append(f'<div class="b-dir" data-kind="dir"><span class="lab">{label}</span>{body}</div>')
        elif block.kind == "quote":
            out.append(f'<div class="b-quote" data-kind="quote">{inline(block.text)}</div>')
        elif block.kind == "tcap":
            out.append(f'<div class="b-tcap" data-kind="tcap">{inline(block.text)}</div>')
        elif block.kind == "trow":
            key = inline(block.attrs.get("key", ""))
            value = inline(block.attrs.get("val", ""))
            out.append(f'<div class="b-trow" data-kind="trow"><strong>{key}</strong>'
                       f'{(" — " + value) if value else ""}</div>')
        elif block.kind == "code":
            out.append(f'<div class="b-code" data-kind="code">{html.escape(block.text) or "&nbsp;"}</div>')
        else:
            out.append(f'<div class="b-p" data-kind="p">{inline(block.text)}</div>')
    return "\n".join(out)


def build_html(blocks: list[Block], *, title: str, font_size: float, line_height: float,
               gap: float, per_page: int, cut_line: bool, css: str, js: str) -> str:
    body_class = ("per4" if per_page == 4 else "per2") + ("" if cut_line else " nocut")
    pad_x = 15 if per_page == 2 else 8
    variables = f":root{{--fs:{font_size}pt;--lh:{line_height};--gap:{gap}mm;--pad-x:{pad_x}mm}}"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
{css}
{variables}
</style>
</head>
<body class="{body_class}" data-title="{html.escape(title)}">
<div id="src">
{blocks_to_html(blocks)}
</div>
<div id="deck"></div>
<script>
{js}
</script>
</body>
</html>
"""


# ------------------------------------------------------------------- chrome render

def win_to_wsl(path: str) -> str:
    """'C:\\Program Files\\...' -> '/mnt/c/Program Files/...' so WSL can exec it."""
    match = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if not match:
        return path
    return f"/mnt/{match.group(1).lower()}/" + match.group(2).replace("\\", "/")


def find_browser(explicit: str | None) -> str:
    for candidate in (explicit, os.environ.get("CUECARD_CHROME")):
        if candidate:
            if Path(candidate).exists() or shutil.which(candidate):
                return candidate
            raise SystemExit(f"browser not found: {candidate}")
    for candidate in WIN_CHROME:
        if Path(win_to_wsl(candidate)).exists():
            return win_to_wsl(candidate)
    for name in LINUX_CHROME:
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("no Chrome/Edge found; pass --chrome /path/to/chrome")


def is_windows_exe(browser: str) -> bool:
    return browser.startswith("/mnt/c/") or browser.lower().endswith(".exe")


def to_win_path(path: Path) -> str:
    match = re.match(r"^/mnt/([a-z])/(.*)$", str(path))
    if not match:
        raise SystemExit(f"cannot convert {path} to a Windows path")
    return f"{match.group(1).upper()}:\\" + match.group(2).replace("/", "\\")


def win_url(path: Path) -> str:
    match = re.match(r"^/mnt/([a-z])/(.*)$", str(path))
    return f"file:///{match.group(1).upper()}:/" + match.group(2)


def render_pdf(browser: str, stage: Path, html_path: Path, pdf_path: Path,
               output: Path, keep_html: bool) -> None:
    profile = stage / "profile"
    flags = ["--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
             "--run-all-compositor-stages-before-draw", "--virtual-time-budget=15000"]
    if is_windows_exe(browser):
        args = [browser, *flags, "--user-data-dir=" + to_win_path(profile),
                "--print-to-pdf=" + to_win_path(pdf_path), win_url(html_path)]
    else:
        args = [browser, *flags, f"--user-data-dir={profile}",
                f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
    subprocess.run(args, check=False, capture_output=True)
    shutil.rmtree(profile, ignore_errors=True)
    if not pdf_path.exists():
        raise SystemExit("Chrome wrote no PDF; re-run with --html-only to inspect the page")

    output.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(20):
        try:
            shutil.copyfile(pdf_path, output)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.5)


def dom_report(browser: str, stage: Path, html_path: Path) -> dict:
    """Read the in-page pagination report (card count and per-card fill %) back out."""
    profile = stage / "profile_dom"
    flags = ["--headless=new", "--disable-gpu", "--no-sandbox",
             "--run-all-compositor-stages-before-draw", "--virtual-time-budget=15000",
             "--dump-dom"]
    url = win_url(html_path) if is_windows_exe(browser) else html_path.resolve().as_uri()
    user_dir = ("--user-data-dir=" + to_win_path(profile)) if is_windows_exe(browser) \
        else f"--user-data-dir={profile}"
    proc = subprocess.run([browser, *flags, user_dir, url], check=False, capture_output=True)
    shutil.rmtree(profile, ignore_errors=True)
    dom = proc.stdout.decode("utf-8", "replace")
    match = re.search(r'<div id="report"([^>]*)>', dom)
    if not match:
        return {"warning": "no pagination report in the DOM (the in-page script did not run)"}
    report = {}
    for key, value in re.findall(r'data-([a-z]+)="([^"]*)"', match.group(1)):
        report[key] = value
    if "cards" in report:
        report["cards"] = int(report["cards"])
    if "overfull" in report:
        report["overfull"] = int(report["overfull"])
    if "fill" in report:
        fills = [int(v) for v in report["fill"].split(",") if v]
        report["fill"] = fills
        report["fill_min"] = min(fills) if fills else 0
        report["fill_under_40pct"] = sum(1 for f in fills if f < 40)
    return report


# ---------------------------------------------------------------------- pdf checks

def trim_blank_trailing(pdf: Path) -> int | None:
    """Drop trailing pages with no text (a 297 mm sheet can round into an extra page)."""
    try:
        import pypdf
    except ImportError:
        return None
    reader = pypdf.PdfReader(str(pdf))
    keep = len(reader.pages)
    while keep > 1 and not (reader.pages[keep - 1].extract_text() or "").strip():
        keep -= 1
    if keep == len(reader.pages):
        return keep
    writer = pypdf.PdfWriter()
    for page in reader.pages[:keep]:
        writer.add_page(page)
    temporary = pdf.with_suffix(".trim.pdf")
    with open(temporary, "wb") as handle:
        writer.write(handle)
    for attempt in range(15):
        try:
            os.replace(temporary, pdf)
            return keep
        except PermissionError:
            time.sleep(0.5)
    return keep


def normalize(text: str) -> str:
    """Keep letters and digits only, so a probe survives markdown, wrapping and punctuation."""
    return re.sub(r"[^\w]", "", text)


def verify(pdf: Path, blocks: list[Block]) -> dict:
    """Prove the artifact: A4 portrait, card numbering, and no block lost to clipping.

    Both the head and the tail of every block are probed: a card that was too full
    would clip the bottom of its last block, which a head-only probe would miss.
    """
    try:
        import pypdf
    except ImportError:
        return {"warning": "pypdf missing; geometry and text checks skipped"}
    reader = pypdf.PdfReader(str(pdf))
    texts = [page.extract_text() or "" for page in reader.pages]
    width = float(reader.pages[0].mediabox.width)
    height = float(reader.pages[0].mediabox.height)
    report: dict = {"pages": len(reader.pages), "page_size_pt": [round(width, 1), round(height, 1)],
                    "cards": sum(len(re.findall(r"카드\s*\d+\s*/\s*\d+", text)) for text in texts),
                    "missing": []}
    if not (560 < width < 620 and 800 < height < 880):
        report["error"] = f"page is not A4 portrait ({width:.0f} x {height:.0f} pt)"
    flat = normalize(" ".join(texts))
    for block in blocks:
        if block.kind in ("part", "section", "rule", "tcap"):
            continue
        source = (normalize(block.attrs.get("key", "")) + normalize(block.attrs.get("val", ""))
                  if block.kind == "trow" else normalize(block.text))
        if len(source) < 8:
            continue
        probes = [source[:24]] + ([source[-24:]] if len(source) >= 40 else [])
        for probe in probes:
            if probe not in flat:
                report["missing"].append((block.text or block.attrs.get("key", ""))[:60])
                break
    return report


# ---------------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", required=True, help="script (.md/.markdown/.txt/.docx)")
    parser.add_argument("-o", "--output", required=True, help="output PDF")
    parser.add_argument("--title", help="running title on every card (default: first heading)")
    parser.add_argument("--part", action="append", default=[],
                        help="keep only parts whose H1 text contains this string (repeatable)")
    parser.add_argument("--skip-front", action="store_true",
                        help="drop everything before the first '## ' section (cover/metadata)")
    parser.add_argument("--per-page", type=int, choices=(2, 4), default=2)
    parser.add_argument("--font-size", type=float, default=16.0)
    parser.add_argument("--line-height", type=float, default=1.5)
    parser.add_argument("--paragraph-gap", type=float, default=2.6, help="block gap in mm")
    parser.add_argument("--block-chars", type=int, default=200,
                        help="max characters per emitted block (keeps blocks splittable)")
    parser.add_argument("--keep-breaks", action="store_true",
                        help="keep the source line breaks inside a paragraph")
    parser.add_argument("--no-cut-line", action="store_true")
    parser.add_argument("--css", help="CSS file that overrides assets/cuecards.css")
    parser.add_argument("--chrome", help="browser executable")
    parser.add_argument("--html-only", action="store_true", help="write the print HTML only")
    parser.add_argument("--keep-html", action="store_true")
    parser.add_argument("--dom-report", action="store_true",
                        help="also print the in-page report (cards, sheets, per-card fill %%)")
    parser.add_argument("--report", action="store_true", help="print the JSON verification report")
    args = parser.parse_args()

    source = Path(args.input).expanduser()
    if not source.is_file():
        raise SystemExit(f"input not found: {source}")
    output = Path(args.output).expanduser().resolve()

    blocks = read_script(source, args.block_chars, args.keep_breaks)
    blocks = select_blocks(blocks, args.part, args.skip_front)
    if not any(block.kind in ("p", "li", "dir", "quote", "trow", "sub") for block in blocks):
        raise SystemExit("no script text found in the input")

    first_part = next((block.title for block in blocks if block.kind == "part"), "")
    title = args.title or first_part or source.stem

    css = (Path(args.css).read_text(encoding="utf-8") if args.css
           else (ASSETS / "cuecards.css").read_text(encoding="utf-8"))
    js = (ASSETS / "paginate.js").read_text(encoding="utf-8")
    page = build_html(blocks, title=title, font_size=args.font_size,
                      line_height=args.line_height, gap=args.paragraph_gap,
                      per_page=args.per_page, cut_line=not args.no_cut_line, css=css, js=js)

    browser = find_browser(args.chrome)
    if is_windows_exe(browser):
        stage = Path(os.environ.get("CUECARD_WIN_TMP", DEFAULT_WIN_TMP)) / f"cuecards_{os.getpid()}"
    else:
        stage = output.parent / ".cuecards-build"
    stage.mkdir(parents=True, exist_ok=True)
    html_path = stage / "cuecards.html"
    pdf_path = stage / ("cuecards.pdf" if is_windows_exe(browser) else output.stem + ".pdf")
    html_path.write_text(page, encoding="utf-8", newline="\n")

    if args.html_only:
        print(f"wrote {html_path}\nprint it: A4 portrait, 100 % scale, one page per side")
        return 0

    render_pdf(browser, stage, html_path, pdf_path, output, args.keep_html)

    pages = trim_blank_trailing(output)
    report = verify(output, blocks)
    report.update({"pdf": str(output), "blocks": len(blocks),
                   "size_kb": round(output.stat().st_size / 1024, 1)})
    if pages:
        report["pages"] = pages
    if args.dom_report:
        report["dom"] = dom_report(browser, stage, html_path)
    if args.report:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"created {output} | {report.get('pages')} A4 pages | "
              f"{report.get('cards')} cards | {report['size_kb']} kB")
        if args.dom_report:
            print(json.dumps(report.get("dom", {}), ensure_ascii=False, indent=2))

    if report.get("error"):
        print("CHECK FAILED: " + report["error"], file=sys.stderr)
        return 3
    if report.get("missing"):
        print(f"CHECK FAILED: {len(report['missing'])} block(s) missing from the PDF, "
              f"e.g. {report['missing'][0]!r}\n"
              f"  a block is only lost when it is taller than a whole card: "
              f"lower --font-size or split the source with '---'.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
