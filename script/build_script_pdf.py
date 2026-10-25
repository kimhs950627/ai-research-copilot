#!/usr/bin/env python3
"""Turn 발표대본.md into a clean A4 print page (script/print.html).

No external dependency. Run:
    python3 build_script_pdf.py
Then print print.html to PDF with Chrome.
"""
from __future__ import annotations
import html
import re
from pathlib import Path

SRC = Path(__file__).parent / "발표대본.md"
OUT = Path(__file__).parent / "print.html"

def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s

def convert(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_ul = False
    in_table = False
    while i < len(lines):
        line = lines[i]
        # fenced code
        if line.strip().startswith("```"):
            if in_ul: out.append("</ul>"); in_ul = False
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre class=\"code\">" + html.escape("\n".join(buf)) + "</pre>")
            continue
        # table
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i+1].strip()):
            if in_ul: out.append("</ul>"); in_ul = False
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue
        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if in_ul: out.append("</ul>"); in_ul = False
            lvl = len(m.group(1))
            txt = inline(m.group(2))
            cls = " class=\"part\"" if lvl == 1 else ""
            out.append(f"<h{lvl}{cls}>{txt}</h{lvl}>")
            i += 1
            continue
        # blockquote
        if line.startswith(">"):
            body = [line.lstrip("> ").strip()]
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i].lstrip("> ").strip()); i += 1
            out.append("<blockquote>" + "<br>".join(inline(x) for x in body) + "</blockquote>")
            continue
        # lists
        if re.match(r"^[-*]\s+", line):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append("<li>" + inline(re.sub(r"^[-*]\s+", "", line)) + "</li>")
            i += 1
            continue
        # hr
        if line.strip() == "---":
            if in_ul: out.append("</ul>"); in_ul = False
            out.append("<hr>")
            i += 1
            continue
        # blank
        if not line.strip():
            if in_ul: out.append("</ul>"); in_ul = False
            i += 1
            continue
        # paragraph
        if in_ul: out.append("</ul>"); in_ul = False
        out.append(f"<p>{inline(line)}</p>")
        i += 1
    if in_ul: out.append("</ul>")
    return "\n".join(out)

CSS = """
@page{size:A4;margin:20mm 18mm}
*{box-sizing:border-box}
body{margin:0;background:#F5F6F1;color:#16201A;
  font-family:"Pretendard","Malgun Gothic","Noto Sans KR",sans-serif;
  font-size:10.5pt;line-height:1.72;word-break:keep-all;line-break:strict}
.wrap{max-width:170mm;margin:0 auto;padding:18mm 0 24mm}
h1,h2,h3{font-family:"Noto Serif KR","Batang",Georgia,serif;line-height:1.22;letter-spacing:-.02em}
h1{font-size:24pt;margin:0 0 6mm;padding-bottom:5mm;border-bottom:2px solid #16543A}
h1.part{font-size:18pt;margin:14mm 0 6mm;color:#16543A;page-break-before:always}
h2{font-size:13pt;margin:8mm 0 2mm;page-break-after:avoid}
h3{font-size:12pt;margin:6mm 0 2mm}
p{margin:0 0 3mm}
strong{font-weight:700}
em{font-style:normal;color:#16543A;font-weight:700}
code{font-family:"JetBrains Mono","Consolas",monospace;font-size:.9em;background:#E6E9DD;padding:.1em .3em;border-radius:2px}
blockquote{margin:3mm 0;padding:3mm 4mm;border-left:3px solid #815800;background:#F2E7CF;font-size:9.5pt}
blockquote br{display:none}
table{border-collapse:collapse;width:100%;margin:4mm 0;font-size:9.5pt}
th,td{border-bottom:1px solid rgba(22,32,26,.14);padding:2.2mm 3mm 2.2mm 0;text-align:left}
th{font-size:8pt;letter-spacing:.08em;text-transform:uppercase;color:#5B6159;border-bottom:1px solid rgba(22,32,26,.3)}
hr{border:0;border-top:1px solid rgba(22,32,26,.2);margin:8mm 0}
pre.code{background:#EDF0E7;border-left:3px solid #16543A;padding:3mm 4mm;margin:3mm 0 4mm;\n  font-family:"JetBrains Mono","Consolas",monospace;font-size:9pt;line-height:1.55;white-space:pre-wrap;page-break-inside:avoid}\nul{padding-left:5mm;margin:0 0 4mm}
li{margin-bottom:1.5mm}
a{color:#16543A;text-decoration:none}
.foot{margin-top:12mm;padding-top:4mm;border-top:1px solid rgba(22,32,26,.3);font-size:8pt;color:#5B6159}
@media print{body{background:#fff}.wrap{padding:0}h1.part{page-break-before:always}}
"""

def main():
    md = SRC.read_text(encoding="utf-8")
    body = convert(md)
    OUT.write_text(f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>발표 대본 — AI와 함께 논문 쓰고 발표하기</title><style>{CSS}</style></head>
<body><div class="wrap">{body}
<div class="foot">AI Research Copilot · 김현수 · 2026 · CC BY 4.0</div>
</div></body></html>""", encoding="utf-8")
    print(OUT)

if __name__ == "__main__":
    main()
