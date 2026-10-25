#!/usr/bin/env python3
"""make-deck.py — turn a deck.json outline into a real slide deck.

    make-deck.py <deck.json> --out build/ [--theme deck.tokens.css] [--no-pptx] [--quiet]

Outputs
    build/slides/NN.html      one standalone file per slide (1920×1080) — used for PNG renders
    build/deck.html           all slides + keyboard navigation (←/→, f fullscreen, n notes)
    build/deck-print.html     @page 13.333in × 7.5in, one slide per page — used for the PDF
    build/speaker.md          speaker notes with per-slide and cumulative timings
    build/deck.pptx           16:9, native editable text boxes + shapes + speaker notes
    build/deck.json           the input, copied for reference

Figures are DRAWN (SVG bars/lines, HTML tables, CSS boxes). No image-generation model is used,
because a chart that came out of an image model has unreadable axes, invented numbers and the
"AI slop" look this skill family exists to avoid.

Exit codes: 0 ok, 1 bad input, 2 output problem.

Note: this file's path is the contract — the SKILL.md and the schema describe exactly this I/O.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_THEME = HERE.parent / "assets" / "deck.tokens.css"

TYPES = {"cover", "agenda", "claim", "evidence", "figure", "compare", "quote",
         "timeline", "kpi", "flow", "team", "closing", "appendix", "section"}
FIGURES = {"kpi", "bar", "line", "table", "quote", "compare", "timeline", "flow", "none"}
DEFAULT_THEME_VALUES = {
    "fontDisplay": "Fraunces",
    "fontBody": "Pretendard",
    "accent": "B33A0B",
    "surface": "FBFAF8",
    "ink": "14120F",
    "muted": "C9C2B8",
}


def inline_md(text) -> str:
    """이스케이프한 뒤 아주 작은 인라인 마크다운만 HTML 로 바꾼다.
    **굵게** → <b>, *기울임* → <i>, `코드` → <code>. 나머지는 글자 그대로."""
    s = esc(text)
    s = re.sub(r"\*\*([^*\n]{1,200}?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]{1,120}?)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"`([^`\n]{1,160})`", r"<code>\1</code>", s)
    return s


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


# ── figures ──────────────────────────────────────────────────────────────────
def fig_kpi(items, unit="") -> str:
    cells = []
    for it in items:
        if isinstance(it, dict):
            v, label = it.get("value", ""), it.get("label", "")
        else:
            v, label = it, ""
        cells.append(f'<li><span class="kpi__value">{esc(v)}{esc(unit)}</span>'
                     f'<span class="kpi__label">{esc(label)}</span></li>')
    return '<ul class="kpis">' + "".join(cells) + "</ul>"


def fig_bar(items, unit="", emphasis=None) -> str:
    pairs = [(it.get("label", ""), float(it.get("value", 0))) for it in items]
    if not pairs:
        return ""
    W, H, baseline, top = 1400, 470, 400, 40
    maxv = max(v for _, v in pairs) or 1.0
    slot = W / len(pairs)
    bw = min(230.0, slot * 0.44)
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{" vs ".join(f"{l} {v}{unit}" for l, v in pairs)}" '
           f'preserveAspectRatio="xMinYMin meet">']
    out.append(f'<line x1="0" y1="{baseline}" x2="{W}" y2="{baseline}" '
               f'stroke="var(--chart-axis)" stroke-width="2"/>')
    for i, (label, val) in enumerate(pairs):
        h = max(2.0, (val / maxv) * (baseline - top))
        x = slot * i + (slot - bw) / 2
        y = baseline - h
        fill = "var(--color-accent)" if emphasis == i else "var(--color-muted-bar)"
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h:.0f}" fill="{fill}"/>')
        out.append(f'<text class="chart__value" x="{x + bw / 2:.0f}" y="{y - 18:.0f}" '
                   f'text-anchor="middle">{esc(fmt_num(val))}{esc(unit)}</text>')
        out.append(f'<text class="chart__label" x="{x + bw / 2:.0f}" y="{baseline + 46:.0f}" '
                   f'text-anchor="middle">{esc(label)}</text>')
    out.append("</svg>")
    return "".join(out)


def fig_line(items, unit="", emphasis=None) -> str:
    pairs = [(it.get("label", ""), float(it.get("value", 0))) for it in items]
    if len(pairs) < 2:
        return fig_bar(items, unit, emphasis)
    W, H, baseline, top = 1400, 470, 400, 40
    vals = [v for _, v in pairs]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pad = span * 0.15
    lo, hi = lo - pad, hi + pad
    step = W / (len(pairs) - 1)
    pts = []
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{" vs ".join(f"{l} {v}{unit}" for l, v in pairs)}">']
    for g in range(4):
        y = top + (baseline - top) * g / 3
        out.append(f'<line x1="0" y1="{y:.0f}" x2="{W}" y2="{y:.0f}" '
                   f'stroke="var(--chart-grid)" stroke-width="1"/>')
    for i, (label, val) in enumerate(pairs):
        x = step * i
        y = baseline - (val - lo) / (hi - lo) * (baseline - top)
        pts.append(f"{x:.0f},{y:.0f}")
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{8 if emphasis == i else 6}" '
                   f'fill="{"var(--color-accent)" if emphasis == i else "var(--color-text-2)"}"/>')
        out.append(f'<text class="chart__value" x="{x:.0f}" y="{y - 22:.0f}" '
                   f'text-anchor="middle">{esc(fmt_num(val))}{esc(unit)}</text>')
        out.append(f'<text class="chart__label" x="{x:.0f}" y="{baseline + 46:.0f}" '
                   f'text-anchor="middle">{esc(label)}</text>')
    out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="var(--color-text-2)" '
               f'stroke-width="4"/>')
    out.append("</svg>")
    return "".join(out)


def fig_table(fig) -> str:
    data = fig.get("data") or {}
    headers = data.get("headers") or []
    rows = data.get("rows") or []
    head = "".join(f"<th scope=\"col\">{inline_md(h)}</th>" for h in headers)
    body = []
    for r in rows:
        cells = "".join(f"<td>{inline_md(c)}</td>" for c in r)
        body.append(f"<tr>{cells}</tr>")
    return (f'<table class="tbl"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')


def fig_compare(fig) -> str:
    data = fig.get("data") or {}
    cols = []
    for side in ("left", "right"):
        s = data.get(side) or {}
        items = "".join(f"<li>{inline_md(x)}</li>" for x in (s.get("items") or []))
        cols.append(f'<div class="cmp__col"><h3>{esc(s.get("title", ""))}</h3>'
                    f'<ul>{items}</ul></div>')
    return f'<div class="cmp">{"".join(cols)}</div>'


def fig_quote(fig) -> str:
    data = fig.get("data")
    if isinstance(data, dict):
        text, cite = data.get("text", ""), data.get("cite", "")
    else:
        text, cite = (data or ""), ""
    return f'<blockquote class="quote"><p>“{esc(text)}”</p><cite>{esc(cite)}</cite></blockquote>'


def fig_timeline(items) -> str:
    lis = []
    for it in items:
        title = it.get("title", it.get("label", "")) if isinstance(it, dict) else it
        meta = it.get("meta", it.get("date", "")) if isinstance(it, dict) else ""
        lis.append(f'<li><span class="tl__meta">{esc(meta)}</span>'
                   f'<span class="tl__title">{esc(title)}</span></li>')
    return f'<ol class="tl">{"".join(lis)}</ol>'


def fig_flow(items) -> str:
    boxes = []
    for it in items:
        title = it.get("title", "") if isinstance(it, dict) else it
        body = it.get("body", "") if isinstance(it, dict) else ""
        boxes.append(f'<li><span class="flow__t">{esc(title)}</span>'
                     f'<span class="flow__b">{esc(body)}</span></li>')
    return f'<ol class="flow">{"".join(boxes)}</ol>'


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v)):,}"
    return f"{v:,.1f}"


def render_figure(fig) -> str:
    if not isinstance(fig, dict):
        return ""
    kind = fig.get("kind", "none")
    data = fig.get("data")
    unit = fig.get("unit", "") or ""
    em = fig.get("emphasis")
    if kind in ("bar", "line", "kpi", "timeline", "flow") and not isinstance(data, list):
        data = [] if data is None else data
    if kind == "kpi":
        return fig_kpi(data or [], unit)
    if kind == "bar":
        return fig_bar(data or [], unit, em)
    if kind == "line":
        return fig_line(data or [], unit, em)
    if kind == "table":
        return fig_table(fig)
    if kind == "compare":
        return fig_compare(fig)
    if kind == "quote":
        return fig_quote(fig)
    if kind == "timeline":
        return fig_timeline(data or [])
    if kind == "flow":
        return fig_flow(data or [])
    return ""


# ── slide rendering ──────────────────────────────────────────────────────────
def slide_body_html(slide, idx, total, theme) -> str:
    t = slide.get("type", "claim")
    kicker = slide.get("kicker", "")
    title = slide.get("title", "")
    lede = slide.get("lede", "")
    body = slide.get("body") or []
    fig = slide.get("figure")
    source = (fig or {}).get("source", "") if isinstance(fig, dict) else ""
    footnote = slide.get("footnote", "")

    parts = []
    if t in ("cover", "section", "closing"):
        parts.append('<div class="cover">')
        if kicker:
            parts.append(f'<p class="cover__kicker">{esc(kicker)}</p>')
        parts.append(f'<h1 class="cover__title">{inline_md(title)}</h1>')
        if lede:
            parts.append(f'<p class="cover__lede">{inline_md(lede)}</p>')
        if t == "cover":
            who = " · ".join(x for x in (theme.get("author", ""), theme.get("org", "")) if x)
            if who:
                parts.append(f'<p class="cover__who">{esc(who)}</p>')
            ev = " · ".join(x for x in (theme.get("event", ""), theme.get("date", "")) if x)
            if ev:
                parts.append(f'<p class="cover__event">{esc(ev)}</p>')
        parts.append("</div>")
        return "".join(parts)

    head = ['<header class="slide__head">']
    if kicker:
        head.append(f'<p class="slide__kicker">{esc(kicker)}</p>')
    head.append(f'<h2 class="slide__title">{inline_md(title)}</h2>')
    if lede:
        head.append(f'<p class="slide__lede">{inline_md(lede)}</p>')
    head.append("</header>")
    parts.append("".join(head))

    content = []
    if isinstance(fig, dict) and fig.get("kind") not in (None, "none"):
        content.append(f'<div class="slide__figure">{render_figure(fig)}</div>')
    if body:
        lis = "".join(f"<li>{inline_md(b)}</li>" for b in body)
        cls = "bullets bullets--tight" if isinstance(fig, dict) and fig.get("kind") != "none" else "bullets"
        content.append(f'<ul class="{cls}">{lis}</ul>')
    if content:
        parts.append(f'<div class="slide__body">{"".join(content)}</div>')
    if source or footnote:
        parts.append(f'<p class="slide__source">{esc(source or footnote)}</p>')
    return "".join(parts)


STRUCT_CSS = """
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--color-surface-0);color:var(--color-text-1);
  font-family:var(--font-body);font-size:var(--text-body);line-height:var(--leading-body);
  -webkit-font-smoothing:antialiased;font-kerning:normal;
  word-break:keep-all;line-break:strict;overflow-wrap:break-word}
.slide{position:relative;width:var(--stage-w);height:var(--stage-h);
  padding:var(--stage-pad-y) var(--stage-pad-x);display:flex;flex-direction:column;
  background:var(--color-surface-0);overflow:hidden}
.slide::before{content:"";position:absolute;left:var(--stage-pad-x);top:calc(var(--stage-pad-y) - 34px);
  width:96px;height:var(--rule);background:var(--color-accent)}
.slide__head{flex:0 0 auto;max-width:1520px}
.slide__kicker{font-size:var(--text-caption);letter-spacing:.16em;text-transform:uppercase;
  color:var(--color-text-3);margin:0 0 var(--space-3)}
.slide__title{font-family:var(--font-display);font-size:var(--text-h2);
  line-height:var(--leading-heading);letter-spacing:var(--tracking-heading);margin:0;text-wrap:balance}
.slide__lede{font-size:var(--text-small);color:var(--color-text-2);margin:var(--space-4) 0 0;max-width:1400px}
.slide__body{flex:1 1 auto;display:flex;flex-direction:column;justify-content:center;
  gap:var(--space-6);min-height:0;padding-top:var(--space-6)}
.slide__figure{width:100%;display:flex;justify-content:flex-start}
.slide__source{position:absolute;left:var(--stage-pad-x);right:var(--stage-pad-x);
  bottom:calc(var(--stage-pad-y) - 46px);font-size:var(--text-caption);color:var(--color-text-3);margin:0}
.bullets{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:var(--space-4)}
.bullets li{position:relative;padding-left:var(--space-6);max-width:1500px}
.bullets li::before{content:"";position:absolute;left:0;top:.55em;width:14px;height:var(--rule);
  background:var(--color-accent)}
.bullets--tight{gap:var(--space-3)}
.bullets--tight li{font-size:var(--text-small)}
.chart{width:100%;max-width:1440px;height:auto;display:block}
.chart__value{font-family:var(--font-display);font-size:52px;fill:var(--color-text-1);
  font-variant-numeric:tabular-nums}
.chart__label{font-family:var(--font-body);font-size:30px;fill:var(--chart-label)}
.kpis{list-style:none;margin:0;padding:0;display:flex;gap:var(--space-8);flex-wrap:wrap}
.kpis li{display:flex;flex-direction:column;gap:var(--space-2)}
.kpi__value{font-family:var(--font-display);font-size:var(--text-kpi);line-height:1;
  letter-spacing:var(--tracking-display);font-variant-numeric:tabular-nums}
.kpi__label{font-size:var(--text-small);color:var(--color-text-2)}
.tbl{border-collapse:collapse;font-size:var(--text-small);width:100%;max-width:1500px}
.tbl th{text-align:left;font-weight:600;border-bottom:2px solid var(--color-border-strong);
  padding:var(--space-3) var(--space-4)}
.tbl td{padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--color-border);
  font-variant-numeric:tabular-nums}
.cmp{display:flex;gap:var(--space-7);width:100%}
.cmp__col{flex:1 1 0;border-top:var(--rule) solid var(--color-muted-bar);padding-top:var(--space-4)}
.cmp__col:first-child{border-top-color:var(--color-accent)}
.cmp__col h3{font-family:var(--font-display);font-size:var(--text-h3);margin:0 0 var(--space-4)}
.cmp__col ul{margin:0;padding-left:1.1em;font-size:var(--text-small);line-height:1.7}
.quote{margin:0;max-width:1500px}
.quote p{font-family:var(--font-display);font-size:var(--text-h1);line-height:1.25;
  letter-spacing:var(--tracking-heading);margin:0}
.quote cite{display:block;margin-top:var(--space-5);font-size:var(--text-small);
  font-style:normal;color:var(--color-text-3)}
.tl,.flow{list-style:none;margin:0;padding:0;display:flex;gap:var(--space-5);width:100%}
.tl li,.flow li{flex:1 1 0;border-top:var(--rule) solid var(--color-accent);
  padding-top:var(--space-4);display:flex;flex-direction:column;gap:var(--space-2)}
.tl__meta{font-size:var(--text-caption);color:var(--color-text-3);letter-spacing:.08em}
.tl__title,.flow__t{font-size:var(--text-h3);font-family:var(--font-display)}
.flow__b{font-size:var(--text-small);color:var(--color-text-2)}
.cover{display:flex;flex-direction:column;justify-content:center;height:100%;gap:var(--space-3)}
.cover__kicker{font-size:var(--text-small);letter-spacing:.18em;text-transform:uppercase;
  color:var(--color-accent);margin:0}
.cover__title{font-family:var(--font-display);font-size:var(--text-display);line-height:var(--leading-tight);
  letter-spacing:var(--tracking-display);margin:0;max-width:1520px;text-wrap:balance}
.cover__lede{font-size:var(--text-h3);color:var(--color-text-2);margin:var(--space-4) 0 0;max-width:1300px}
.cover__who{font-size:var(--text-small);margin:var(--space-6) 0 0}
.cover__event{font-size:var(--text-caption);color:var(--color-text-3);margin:0}
.slide--section,.slide--closing{background:var(--color-surface-inverse);color:var(--color-text-on-inverse)}
.slide--section .cover__kicker,.slide--closing .cover__kicker{color:var(--color-accent-quiet)}
.slide--section .cover__lede,.slide--closing .cover__lede{color:var(--color-text-on-inverse)}
/* 어두운 슬라이드에서는 캡션 색을 on-inverse 로 바꾼다 (text-3 은 밝은 배경용) */
.slide--section .slide__num,.slide--closing .slide__num,
.slide--section .slide__source,.slide--closing .slide__source,
.slide--section .slide__kicker,.slide--closing .slide__kicker{color:var(--color-text-on-inverse)}
.slide__num{position:absolute;right:var(--stage-pad-x);bottom:calc(var(--stage-pad-y) - 46px);
  font-size:var(--text-caption);color:var(--color-text-3);font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""


def page_html(slide, idx, total, head_extra="", stage_scale=False) -> str:
    cls = f"slide slide--{slide.get('type', 'claim')}"
    return (
        f'<section class="{cls}" id="s{idx}" data-index="{idx}">'
        f'{slide_body_html(slide, idx, total, slide.get("_meta", {}))}'
        f'<span class="slide__num">{idx} / {total}</span>'
        f'</section>'
    )


def standalone(slide, idx, total, css) -> str:
    return f"""<!doctype html>
<html lang="{esc(slide.get('_lang', 'ko'))}">
<head>
<meta charset="utf-8">
<title>{esc(slide.get('title', 'slide'))}</title>
<style>
{css}
html,body{{width:var(--stage-w);height:var(--stage-h);overflow:hidden}}
</style>
</head>
<body>
{page_html(slide, idx, total)}
</body>
</html>
"""


def deck_html(slides, meta, css) -> str:
    total = len(slides)
    body = "".join(page_html(s, i + 1, total) for i, s in enumerate(slides))
    return f"""<!doctype html>
<html lang="{esc(meta.get('lang', 'ko'))}">
<head>
<meta charset="utf-8">
<title>{esc(meta.get('title', 'deck'))}</title>
<style>
{css}
html,body{{margin:0;height:100%;background:var(--color-surface-inverse);overflow:hidden}}
#stage{{position:fixed;inset:0;display:grid;place-items:center}}
#deck{{width:var(--stage-w);height:var(--stage-h);transform-origin:center center;position:relative}}
.slide{{position:absolute;inset:0;display:none}}
.slide.is-active{{display:flex;animation:fade var(--duration-in) var(--ease-out)}}
@keyframes fade{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
#help{{position:fixed;left:16px;bottom:12px;color:#8b8478;font:14px/1.4 system-ui;z-index:10}}
</style>
</head>
<body>
<div id="stage"><div id="deck">{body}</div></div>
<div id="help">← → 이동 · f 전체화면 · n 발표자 노트 · o 개요</div>
<script>
(function(){{
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var i=Math.max(0,Math.min(slides.length-1,(parseInt(location.hash.replace('#s',''),10)||1)-1));
  function scale(){{
    var d=document.getElementById('deck'),s=Math.min(innerWidth/1920,innerHeight/1080);
    d.style.transform='scale('+s+')';
  }}
  function show(n){{
    i=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(el,k){{el.classList.toggle('is-active',k===i);}});
    history.replaceState(null,'','#s'+(i+1));
    if(notesWin&&!notesWin.closed) notesWin.postMessage({{i:i}},'*');
  }}
  var notesWin=null;
  addEventListener('keydown',function(e){{
    if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){{e.preventDefault();show(i+1);}}
    else if(e.key==='ArrowLeft'||e.key==='PageUp'){{e.preventDefault();show(i-1);}}
    else if(e.key==='Home')show(0);
    else if(e.key==='End')show(slides.length-1);
    else if(e.key==='f'){{document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();}}
    else if(e.key==='n'){{notesWin=open('notes.html','notes','width=760,height=520');}}
    else if(e.key==='o'){{document.getElementById('help').style.display=document.getElementById('help').style.display==='none'?'block':'none';}}
  }});
  addEventListener('resize',scale);
  scale();show(i);
}})();
</script>
</body>
</html>
"""


def notes_html(slides, meta) -> str:
    items = json.dumps([
        {"title": s.get("title", ""), "notes": s.get("notes", ""),
         "seconds": s.get("seconds") or 40} for s in slides
    ], ensure_ascii=False)
    return f"""<!doctype html>
<html lang="{esc(meta.get('lang', 'ko'))}">
<head><meta charset="utf-8"><title>발표자 노트</title>
<style>
body{{margin:0;font:18px/1.6 "Pretendard",system-ui;padding:28px 32px;color:#14120F;background:#FBFAF8}}
#t{{font-size:30px;font-weight:700;margin:0 0 8px;font-family:"Fraunces",Georgia,serif}}
#n{{white-space:pre-wrap}}
#m{{color:#857D72;font-size:15px;margin-top:24px}}
</style></head>
<body>
<p id="t"></p><div id="n"></div><p id="m"></p>
<script>
var data={items};var cur=-1;
var total=0;data.forEach(function(d){{total+=d.seconds;}});
addEventListener('message',function(e){{set(e.data.i);}});
function fmt(s){{return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2);}}
function set(i){{
  if(i===cur||!data[i])return;cur=i;
  var d=data[i];document.getElementById('t').textContent=d.title;
  document.getElementById('n').textContent=d.notes||'(노트 없음)';
  var acc=0;for(var k=0;k<=i;k++)acc+=data[k].seconds;
  document.getElementById('m').textContent=
    '슬라이드 '+(i+1)+'/'+data.length+' · 목표 '+d.seconds+'초 · 누적 '+fmt(acc)+' / 전체 '+fmt(total);
}}
set(0);
</script>
</body></html>
"""


def print_html(slides, meta, css) -> str:
    body = "".join(page_html(s, i + 1, len(slides)) for i, s in enumerate(slides))
    return f"""<!doctype html>
<html lang="{esc(meta.get('lang', 'ko'))}">
<head>
<meta charset="utf-8">
<title>{esc(meta.get('title', 'deck'))}</title>
<style>
{css}
@page {{ size: 13.333in 7.5in; margin: 0; }}
html,body{{margin:0;background:#fff}}
.slide{{break-after:page;page-break-after:always;width:var(--stage-w);height:var(--stage-h)}}
.slide:last-child{{break-after:auto;page-break-after:auto}}
@media print{{ .slide__num{{display:none}} }}
</style>
</head>
<body>{body}</body>
</html>
"""


def speaker_md(slides, meta) -> str:
    lines = [f"# {meta.get('title', '')} — 발표자 노트", ""]
    if meta.get("event") or meta.get("date"):
        lines.append(f"{meta.get('event', '')} · {meta.get('date', '')}".strip(" ·"))
        lines.append("")
    if meta.get("author"):
        lines += [f"발표자: {meta['author']}", ""]
    target = meta.get("durationMin")
    total_sec = sum((s.get("seconds") or 40) for s in slides)
    lines += [f"- 슬라이드: **{len(slides)}장**",
              f"- 목표 시간: **{('%.1f분' % target) if target else '미지정'}**",
              f"- 노트 합계: **{total_sec // 60}분 {total_sec % 60}초**"
              + ("  ← 목표 대비 초과/부족을 확인" if target else ""),
              "- 청중 유형: **%s**" % meta.get("audience", ""),
              ""]
    acc = 0
    for i, s in enumerate(slides, 1):
        sec = s.get("seconds") or 40
        acc += sec
        lines += [f"## {i:02d} — {s.get('title', '')}",
                  f"**목표 {sec}초** · 누적 {acc // 60}:{acc % 60:02d} / 유형 `{s.get('type', '')}`", ""]
        for b in (s.get("body") or []):
            lines.append(f"- {b}")
        if s.get("notes"):
            lines += ["", s["notes"]]
        else:
            lines += ["", "> 노트 없음 — 핵심 한 문장 · 말할 것 · 하지 말 것 · 전환 문장을 채운다."]
        lines.append("")
    lines += ["## 마지막 점검", "",
              "- [ ] 첫 30초와 마지막 30초를 외웠다",
              "- [ ] 자를 순서를 정했다 (보통 방법 세부 → 부록)",
              "- [ ] 예상 질문 5개와 부록 번호를 연결했다",
              "- [ ] 발표 PC 에서 폰트·해상도·노트 창을 확인했다"]
    return "\n".join(lines)


# ── PPTX ─────────────────────────────────────────────────────────────────────
def build_pptx(slides, meta, out: Path, theme: dict) -> str | None:
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.util import Emu, Inches, Pt
    except Exception as e:  # pragma: no cover
        return f"python-pptx 없음 ({e})"

    def rgb(hexstr, fallback):
        raw = re.sub(r"[^0-9a-fA-F]", "", str(hexstr or fallback))[:6].ljust(6, "0")
        return RGBColor.from_string(raw.upper())

    surf = rgb(theme.get("surface"), "FBFAF8")
    ink = rgb(theme.get("ink"), "14120F")
    accent = rgb(theme.get("accent"), "B33A0B")
    muted = rgb(theme.get("muted"), "C9C2B8")
    f_display = theme.get("fontDisplay") or DEFAULT_THEME_VALUES["fontDisplay"]
    f_body = theme.get("fontBody") or DEFAULT_THEME_VALUES["fontBody"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def textbox(slide, x, y, w, h, lines, size, font, color, bold=False, align=None):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = str(line)
            for r in p.runs:
                r.font.size = Pt(size)
                r.font.name = font
                r.font.bold = bold
                r.font.color.rgb = color
            if align:
                p.alignment = align
        return tb

    for i, s in enumerate(slides, 1):
        sl = prs.slides.add_slide(blank)
        # background
        bg = sl.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = rgb(theme.get("surface"), "FBFAF8") if s.get("type") not in (
            "section", "closing") else ink
        bg.line.fill.background()
        fg = ink if s.get("type") not in ("section", "closing") else rgb("F3EFE9", "F3EFE9")
        # accent rule
        rule = sl.shapes.add_shape(1, Inches(0.6), Inches(0.5), Inches(0.7), Pt(3))
        rule.fill.solid(); rule.fill.fore_color.rgb = accent; rule.line.fill.background()

        kicker = s.get("kicker", "")
        if kicker:
            textbox(sl, 0.6, 0.72, 12.1, 0.35, [kicker.upper()], 11, f_body, muted)

        coverish = s.get("type") in ("cover", "section", "closing")
        title_size = 34 if coverish else 26
        textbox(sl, 0.6, 1.05, 12.1, 1.7, [s.get("title", "")], title_size, f_display, fg, True)

        y = 2.85 if coverish else 2.55
        if s.get("lede") and not coverish:
            textbox(sl, 0.6, y, 12.1, 0.5, [s["lede"]], 15, f_body, muted)
            y += 0.5

        fig = s.get("figure") if isinstance(s.get("figure"), dict) else None
        body = s.get("body") or []
        if body:
            textbox(sl, 0.6, y, 11.0, 2.4, [f"· {b}" for b in body], 15, f_body, fg)
            y += min(2.4, 0.4 * len(body) + 0.3)

        if fig:
            kind, data = fig.get("kind"), fig.get("data")
            unit = fig.get("unit", "") or ""
            if kind == "kpi" and isinstance(data, list):
                textbox(sl, 0.6, y, 12.1, 1.2,
                        ["   ".join(f"{d.get('value','')}{unit}" for d in data if isinstance(d, dict))],
                        40, f_display, fg, True)
                labels = "   ".join(d.get("label", "") for d in data if isinstance(d, dict))
                textbox(sl, 0.6, y + 1.0, 12.1, 0.4, [labels], 12, f_body, muted)
            elif kind == "bar" and isinstance(data, list) and data:
                vals = [float(d.get("value", 0)) for d in data if isinstance(d, dict)]
                maxv = max(vals) or 1.0
                barw = min(1.2, 10.0 / max(1, len(vals)) * 0.45)
                gap = (11.0 - barw * len(vals)) / max(1, len(vals))
                base = 6.3
                for k, d in enumerate(data):
                    if not isinstance(d, dict):
                        continue
                    h = max(0.1, float(d.get("value", 0)) / maxv * 3.4)
                    x = 0.8 + k * (barw + gap)
                    rect = sl.shapes.add_shape(1, Inches(x), Inches(base - h), Inches(barw), Inches(h))
                    rect.fill.solid()
                    rect.fill.fore_color.rgb = accent if fig.get("emphasis") == k else muted
                    rect.line.fill.background()
                    textbox(sl, x - 0.2, base - h - 0.42, barw + 0.4, 0.35,
                            [f"{d.get('value','')}{unit}"], 13, f_display, fg, True, PP_ALIGN.CENTER)
                    textbox(sl, x - 0.3, base + 0.05, barw + 0.6, 0.5,
                            [d.get("label", "")], 10, f_body, muted, False, PP_ALIGN.CENTER)
            elif kind == "table" and isinstance(data, dict):
                rows = data.get("rows") or []
                heads = data.get("headers") or []
                shape = sl.shapes.add_table(len(rows) + 1, max(1, len(heads)), Inches(0.6), Inches(y),
                                            Inches(12.1), Inches(0.35 * (len(rows) + 1)))
                tbl = shape.table
                for c, h in enumerate(heads):
                    tbl.cell(0, c).text = str(h)
                    for p in tbl.cell(0, c).text_frame.paragraphs:
                        for r in p.runs:
                            r.font.size = Pt(12); r.font.bold = True; r.font.name = f_body
                for ri, row in enumerate(rows, 1):
                    for ci, cell in enumerate(row[:len(heads)] if heads else row):
                        tbl.cell(ri, ci).text = str(cell)
                        for p in tbl.cell(ri, ci).text_frame.paragraphs:
                            for r in p.runs:
                                r.font.size = Pt(11); r.font.name = f_body
            elif kind in ("timeline", "flow") and isinstance(data, list):
                lines = [f"{d.get('meta','')} {inline_md(d.get('title',''))}".strip() if isinstance(d, dict)
                         else str(d) for d in data]
                textbox(sl, 0.6, y, 12.1, 1.6, [" → ".join(lines)], 14, f_body, fg)
            elif kind == "compare" and isinstance(data, dict):
                left = data.get("left") or {}
                right = data.get("right") or {}
                textbox(sl, 0.6, y, 5.8, 2.2, [left.get("title", "")] + list(left.get("items") or []),
                        13, f_body, fg, True if False else False)
                textbox(sl, 6.9, y, 5.8, 2.2, [right.get("title", "")] + list(right.get("items") or []),
                        13, f_body, fg)
            elif kind == "quote":
                q = data.get("text") if isinstance(data, dict) else data
                cite = data.get("cite", "") if isinstance(data, dict) else ""
                textbox(sl, 0.6, y, 12.1, 1.6, [f"“{q}”"], 20, f_display, fg, True)
                if cite:
                    textbox(sl, 0.6, y + 1.5, 12.1, 0.4, [cite], 11, f_body, muted)

        source = (fig or {}).get("source") or s.get("footnote") or ""
        if source:
            textbox(sl, 0.6, 6.95, 12.1, 0.35, [source], 10, f_body, muted)

        if s.get("notes"):
            sl.notes_slide.notes_text_frame.text = str(s["notes"])

    prs.save(str(out))
    return None


# ── main ─────────────────────────────────────────────────────────────────────
def main(argv) -> int:
    ap = argparse.ArgumentParser(description="make-deck.py — deck.json → HTML/PNG/PDF/PPTX")
    ap.add_argument("deck", type=Path)
    ap.add_argument("--out", type=Path, default=Path("build"))
    ap.add_argument("--theme", type=Path, default=None)
    ap.add_argument("--html-only", "--no-pptx", dest="html_only", action="store_true",
                    help="skip the PPTX (default: build HTML AND PPTX)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv[1:])

    if not a.deck.is_file():
        print(f"make-deck.py: no such deck: {a.deck}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(a.deck.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"make-deck.py: invalid JSON in {a.deck}: {e}", file=sys.stderr)
        return 1

    meta = doc.get("meta") or {}
    slides = doc.get("slides") or []
    if not slides:
        print("make-deck.py: deck.json has no slides", file=sys.stderr)
        return 1
    bad = [s.get("type") for s in slides if s.get("type") not in TYPES]
    if bad:
        print(f"make-deck.py: unknown slide type(s): {bad} — allowed: {sorted(TYPES)}",
              file=sys.stderr)
        return 1
    for s in slides:
        s["_meta"] = meta
        s["_lang"] = meta.get("lang", "ko")

    theme_file = a.theme or DEFAULT_THEME
    try:
        tokens = theme_file.read_text(encoding="utf-8")
    except OSError as e:
        print(f"make-deck.py: cannot read theme {theme_file}: {e}", file=sys.stderr)
        return 1

    header = f"/* generated by make-deck.py from {theme_file.name} */\n"
    css = header + tokens + "\n" + STRUCT_CSS

    out = a.out
    try:
        (out / "slides").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"make-deck.py: cannot create {out}: {e}", file=sys.stderr)
        return 2

    for i, s in enumerate(slides, 1):
        (out / "slides" / f"{i:02d}.html").write_text(standalone(s, i, len(slides), css),
                                                      encoding="utf-8")
    (out / "deck.html").write_text(deck_html(slides, meta, css), encoding="utf-8")
    (out / "notes.html").write_text(notes_html(slides, meta), encoding="utf-8")
    (out / "deck-print.html").write_text(print_html(slides, meta, css), encoding="utf-8")
    (out / "speaker.md").write_text(speaker_md(slides, meta), encoding="utf-8")
    shutil.copyfile(a.deck, out / "deck.json")

    pptx_note = "skipped (--html-only)"
    if not a.html_only:
        err = build_pptx(slides, meta, out / "deck.pptx", meta.get("theme") or {})
        pptx_note = "ok" if err is None else f"failed: {err}"

    if not a.quiet:
        total = sum((s.get("seconds") or 40) for s in slides)
        print(f"make-deck.py: {len(slides)} slides → {out}")
        print(f"  HTML : deck.html (발표 화면) · deck-print.html (PDF용) · notes.html (발표자 노트 창)")
        print(f"         slides/01..{len(slides):02d}.html (PNG 렌더용)")
        print(f"  PPTX : {pptx_note}")
        print(f"  speaker.md · 노트 합계 {total // 60}분 {total % 60}초"
              + (f" / 목표 {meta['durationMin']}분" if meta.get("durationMin") else ""))
        print(f"  다음: render-deck.sh {out} --pdf {out}/deck.pdf --png")
        print(f"        deck-check.sh {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
