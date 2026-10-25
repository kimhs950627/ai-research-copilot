#!/usr/bin/env python3
"""Build the tutorial deck: slides/NN.html + index.html + deck-print.html.

Content lives in SLIDES below. Run from this folder:
    python3 build_deck.py
"""
from __future__ import annotations
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "slides"
OUT.mkdir(exist_ok=True)

HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1920, initial-scale=1">
<title>{title} — AI와 함께 논문 쓰고 발표하기</title>
<link rel="stylesheet" href="../tokens.css">
<link rel="stylesheet" href="../deck.css">
</head>
<body class="slide-page">
<section class="slide {cls}" data-index="{idx}">
{body}
</section>
</body>
</html>
"""

# ── helpers ──────────────────────────────────────────────────────────────
def head(kicker: str, title: str, sub: str = "") -> str:
    s = f'<div class="slide__kicker">{kicker}</div>\n<h1 class="slide__title">{title}</h1>'
    if sub:
        s += f'\n<p class="slide__sub">{sub}</p>'
    return s

def source(text: str) -> str:
    return f'<div class="slide__source">{text}</div>'

def footer(n: int, label: str) -> str:
    return (f'<div class="slide__foot"><span>{label}</span>'
            f'<span class="slide__num">{n:02d} / 17</span></div>')

# ── slides ───────────────────────────────────────────────────────────────
SLIDES: list[dict] = []

def add(title, body, cls="", label=""):
    SLIDES.append(dict(title=title, body=body, cls=cls, label=label))

# 01 cover
add("표지", """
<div class="cover__top"><span class="cover__event">2026 대한가정의학회 추계학술대회 · 수상 기념</span><span class="cover__tag">동료 연구자를 위한 안내</span></div>
<div class="cover__main">
  <div class="slide__kicker">Research workflow · 2026</div>
  <h1 class="cover__title">AI와 함께<br>논문 쓰고<br>발표하기</h1>
  <p class="cover__sub">한 폴더 · 일곱 스킬 · 여덟 단계<br>국민건강영양조사 데이터로 하는 연구를 위한 실전 워크플로</p>
</div>
<div class="cover__who"><span>김현수 · 가정의학과</span><span>약 20분</span><span>github.com/kimhs950627/ai-research-copilot</span></div>
""", cls="slide--cover", label="표지")

# 02 statement
add("이 발표의 목적", """
<div class="slide__kicker">먼저 드릴 말씀</div>
<h1 class="slide__title">상을 받은 것은 결과지만,<br>오늘 드릴 것은 <em>과정</em>입니다.</h1>
<div class="slide__body narrow">
  <p>2026년 7월부터 10월까지, 저는 논문 한 편과 발표 하나를 만들었습니다.</p>
  <p>그 과정에서 쓴 <strong>폴더·프롬프트·검증 순서</strong>를 그대로 남겼습니다. 여러분의 데이터는 이미지가 아니라 표이지만, 일하는 방식은 같습니다.</p>
</div>
<div class="slide__source">HCC vs 혈관종 · B-mode 초음파 · 공개 데이터셋(SMC-LUD) · 2026</div>
""", label="서론")

# 03 problem
add("문제", """
<div class="slide__kicker">왜 시간이 부족한가</div>
<h1 class="slide__title">연구는 절반,<br>문서와 발표가 나머지 절반입니다</h1>
<div class="slide__body">
  <div class="bars">
    <div class="bar"><span class="bar__label">연구·분석</span><span class="bar__track"><i style="width:42%"></i></span><span class="bar__val">가장 중요한 일</span></div>
    <div class="bar"><span class="bar__label">원고·표·그림</span><span class="bar__track"><i style="width:34%"></i></span><span class="bar__val">반복·형식의 일</span></div>
    <div class="bar"><span class="bar__label">발표 준비</span><span class="bar__track"><i style="width:24%"></i></span><span class="bar__val">마감 직전에 몰림</span></div>
  </div>
  <p class="lede-sm">AI가 줄여 주는 것은 <strong>아래 두 줄</strong>입니다. 연구 자체가 빨라지지는 않습니다.</p>
</div>
<div class="slide__source">저자의 체감 비중이며, 측정된 연구 자료가 아닙니다.</div>
""", label="문제")

# 04 chatbot vs agent
add("작동 원리", """
<div class="slide__kicker">오해부터 풉니다</div>
<h1 class="slide__title">챗봇은 말하고,<br>에이전트는 파일을 고칩니다</h1>
<div class="slide__body">
  <div class="cmp">
    <div class="cmp__col"><div class="cmp__head">챗봇</div><ul class="bullets"><li>복사 → 붙여넣기 → 다시 복사</li><li>파일을 볼 수 없음</li><li>결과가 내 컴퓨터에 남지 않음</li></ul></div>
    <div class="cmp__col cmp__col--on"><div class="cmp__head">에이전트 (OpenCode)</div><ul class="bullets"><li>폴더를 열면 파일을 읽고 고침</li><li>코드를 실행해 표·그림 생성</li></ul></div>
  </div>
</div>
<div class="slide__source">핵심 차이는 “대화가 결과물”이 아니라 “폴더가 결과물”이라는 점입니다.</div>
""", label="원리")

# 05 workflow
add("여덟 단계", """
<div class="slide__kicker">전체 지도</div>
<h1 class="slide__title">질문에서 큐카드까지,<br>여덟 단계</h1>
<div class="slide__body">
  <div class="flow">
    <div><b>01</b>질문을 계약서로</div><div><b>02</b>자료·문헌 한곳에</div><div><b>03</b>분석 계획 고정</div><div><b>04</b>표 1 · 주 분석</div>
    <div><b>05</b>원고 IMRaD</div><div><b>06</b>자체 심사</div><div><b>07</b>투고 패키지</div><div><b>08</b>발표 · 큐카드</div>
  </div>
  <p class="lede-sm">3단계를 건너뛰면, 표가 나온 뒤에 질문을 바꾸게 됩니다.</p>
</div>
""", label="워크플로")

# 06 skills
add("스킬", """
<div class="slide__kicker">일곱 개의 업무 매뉴얼</div>
<h1 class="slide__title">스킬은 프롬프트가 아니라<br>절차서입니다</h1>
<div class="slide__body">
  <table class="tbl">
    <thead><tr><th>스킬</th><th>하는 일</th><th>부르는 때</th></tr></thead>
    <tbody>
      <tr><td><code>academic-research-writing</code></td><td>원고·근거 장부·인용 검증</td><td>문헌고찰, IMRaD</td></tr>
      <tr><td><code>deep-research</code></td><td>조사·비교·팩트체크</td><td>배경, 가이드라인</td></tr>
      <tr><td><code>paper-review</code></td><td>제출 전 자체 심사</td><td>투고 1주 전</td></tr>
      <tr><td><code>design-craft</code></td><td>색·타이포·여백·검사</td><td>PDF·포스터</td></tr>
      <tr><td><code>deck-craft</code></td><td>16:9 덱·노트·PPTX</td><td>학회 발표</td></tr>
      <tr><td><code>script-to-cuecards</code></td><td>대본 → 인쇄용 카드</td><td>리허설</td></tr>
      <tr><td><code>clinical-prescribing-safety</code></td><td>처방·금기·상호작용</td><td>임상 질문</td></tr>
    </tbody>
  </table>
</div>
""", label="스킬")

# 07 PICO
add("1단계", """
<div class="slide__kicker">Step 1 · 질문</div>
<h1 class="slide__title">“알아보고자 했다”는<br>질문이 아닙니다</h1>
<div class="slide__body">
  <div class="pico">
    <div><b>P</b><span>40세 이상 성인</span></div>
    <div><b>I</b><span>복부비만</span></div>
    <div><b>C</b><span>복부비만 없음</span></div>
    <div><b>O</b><span>대사증후군</span></div>
  </div>
  <p class="quote-line">“국민건강영양조사에서 40세 이상 성인의 복부비만과<br>대사증후군의 연도별 연관은 어떠한가?”</p>
  <p class="lede-sm">질문·설계·주 결과·보고 지침을 <code>notes/decision.md</code>에 10줄로 적으면 1단계 끝.</p>
</div>
""", label="1단계")

# 08 KNHANES
add("2단계", """
<div class="slide__kicker">Step 4 · 국민건강영양조사</div>
<h1 class="slide__title">가중치를 빼면<br>그 숫자는 한국의 값이 아닙니다</h1>
<div class="slide__body">
  <div class="two-col">
    <div>
      <ul class="bullets big">
        <li>층 <code>kstrata</code> · 집락 <code>psu</code> · 가중치 <code>wt_*</code></li>
        <li>가중치를 빼면 젊은 층이 과대표</li>
        <li>층·집락을 빼면 <strong>p값이 실제보다 작아짐</strong></li>
        <li>변수명은 <strong>연도·파일마다 다름</strong></li>
      </ul>
    </div>
    <div class="codebox">
      <div class="codebox__head">R · survey</div>
      <pre>des &lt;- svydesign(
  ids = ~psu, strata = ~kstrata,
  weights = ~wt_exam,
  nest = TRUE, data = raw)</pre>
    </div>
  </div>
  <p class="lede-sm">매 프롬프트에 붙이세요: <strong>“복합표본설계를 반영하고, 변수명은 코드북에서 확인해.”</strong></p>
</div>
<div class="slide__source">변수명은 예시이며, 실제 이름은 코드북에서 확인해야 합니다.</div>
""", label="KNHANES")

# 09 tables
add("5단계", """
<div class="slide__kicker">Step 5 · 원고</div>
<h1 class="slide__title">표가 먼저,<br>문장은 나중입니다</h1>
<div class="slide__body">
  <div class="two-col">
    <div>
      <p class="bad-line">나쁜 문장</p>
      <p class="quote-line muted">“복부비만군에서 대사증후군 유병률이 42.3%로 비복부비만군의 21.7%보다 유의하게 높았다(p&lt;0.001).”</p>
    </div>
    <div>
      <p class="good-line">좋은 문장</p>
      <p class="quote-line">“복부비만군에서 대사증후군 유병률이 더 높았으며, 추정치는 표 2에 제시하였다.”</p>
    </div>
  </div>
  <p class="lede-sm">문장 하나에 숫자는 최대 하나. 나머지는 <strong>표를 가리킵니다.</strong></p>
</div>
""", label="원고")

# 10 review
add("6단계", """
<div class="slide__kicker">Step 6 · 제출 전</div>
<h1 class="slide__title">심사자를 먼저 부릅니다</h1>
<div class="slide__body">
  <div class="review">
    <div class="review__col"><div class="review__head high">HIGH</div><ul class="bullets"><li>근거 없는 단정</li><li>표에 없는 숫자</li><li>존재하지 않는 인용</li></ul></div>
    <div class="review__col"><div class="review__head med">MED</div><ul class="bullets"><li>숫자 나열 문단</li><li>표·그림 번호 불일치</li></ul></div>
  </div>
  <p class="lede-sm">고치게 하지 말고, 먼저 <strong>지적</strong>하게 합니다.</p>
</div>
""", label="자체심사")

# 11 package
add("7단계", """
<div class="slide__kicker">Step 7 · 투고</div>
<h1 class="slide__title">제출 화면에서<br>헤매지 않으려면</h1>
<div class="slide__body">
  <div class="two-col">
    <div class="tree">
      <div>04_manuscript/submission/</div>
      <div>├─ 01_title_page.docx</div>
      <div>├─ 02_manuscript_blind.docx</div>
      <div>├─ 03_tables.docx</div>
      <div>├─ 04_figures/</div>
      <div>├─ 05_cover_letter.docx</div>
      <div>└─ 06_coi_ai_statement.docx</div>
    </div>
    <div>
      <ul class="bullets big">
        <li>맹검판·비맹검판 따로</li>
        <li>표·그림은 별도 파일</li>
        <li>AI 사용 공개 문구</li>
        <li>빠진 파일은 “없음”으로 표시</li>
      </ul>
    </div>
  </div>
</div>
""", label="투고")

# 12 talk math
add("8단계", """
<div class="slide__kicker">Step 8 · 발표</div>
<h1 class="slide__title">8분은 13장입니다</h1>
<div class="slide__body">
  <div class="kpis">
    <div class="kpi"><span class="kpi__num">30–45</span><span class="kpi__label">슬라이드당 초</span></div>
    <div class="kpi"><span class="kpi__num">11–14</span><span class="kpi__label">8분 권장 장수</span></div>
    <div class="kpi"><span class="kpi__num">±10%</span><span class="kpi__label">리허설 허용 오차</span></div>
  </div>
  <p class="lede-sm">장수를 늘리는 것보다 <strong>한 장을 오래 보는 편</strong>이 낫습니다. 제 발표는 13장·7분 35초였습니다.</p>
</div>
""", label="발표")

# 13 cuecards
add("8단계", """
<div class="slide__kicker">Step 8 · 대본과 큐카드</div>
<h1 class="slide__title">말할 문장과<br>손에 들 것을 따로 만듭니다</h1>
<div class="slide__body">
  <div class="flow flow--3">
    <div><b>01</b>아웃라인 — 제목 = 주장</div>
    <div><b>02</b>덱 — 한 장에 한 아이디어</div>
    <div><b>03</b>대본 — 시간 붙이기</div>
    <div><b>04</b>큐카드 — A4 두 장 분할</div>
    <div><b>05</b>리허설 — 타이머 3회</div>
  </div>
  <p class="lede-sm">큐카드는 대본을 <strong>줄이지 않습니다.</strong> 넘치면 “계속” 카드로 이어 붙입니다.</p>
</div>
""", label="큐카드")

# 14 case
add("사례", """
<div class="slide__kicker">실제 사례 · HCC vs 혈관종</div>
<h1 class="slide__title">이기지 못한 결과를<br>어떻게 발표했나</h1>
<div class="slide__body">
  <div class="kpis kpis--4">
    <div class="kpi"><span class="kpi__num">95.71</span><span class="kpi__label">민감도 %</span></div>
    <div class="kpi"><span class="kpi__num">100</span><span class="kpi__label">특이도 %</span></div>
    <div class="kpi"><span class="kpi__num">0.125</span><span class="kpi__label">McNemar p</span></div>
    <div class="kpi"><span class="kpi__num">13</span><span class="kpi__label">슬라이드</span></div>
  </div>
  <p class="quote-line">“차이는 유의하지 않습니다. 다만 <strong>실패하는 지점이 다릅니다.</strong>”</p>
  <p class="lede-sm">한계를 먼저 말한 슬라이드가 심사위원의 신뢰를 만들었습니다.</p>
</div>
<div class="slide__source">테스트 268장 · 134/0/6/128 · 정확도 97.76% · 단일 기관 공개 데이터셋.</div>
""", label="사례")

# 15 award questions
add("수상 전략", """
<div class="slide__kicker">상을 목표로 한다면</div>
<h1 class="slide__title">심사위원은 통계보다<br>다음 질문을 합니다</h1>
<div class="slide__body">
  <div class="three-q">
    <div><span class="qnum">Q1</span><h3>IRB는 통과했나요?</h3><p>승인번호·면제 사유를 30초로. “필요 없었어요”가 아니라 “이 근거로 면제받았습니다”.</p></div>
    <div><span class="qnum">Q2</span><h3>계속 연구할 건가요?</h3><p>1년 계획 2문장. “네”보다 “외부 검증 → 전향 코호트 → 다기관”.</p></div>
    <div><span class="qnum">Q3</span><h3>임상에서 어디에 쓰나요?</h3><p>판독 대체가 아니라 <strong>워크플로의 한 칸</strong>을 지정.</p></div>
  </div>
</div>
<div class="slide__source">2026 대한가정의학회 추계학술대회 발표에서 실제로 받은 질문 유형.</div>
""", label="수상전략")

# 16 data strategy
add("수상 전략", """
<div class="slide__kicker">어떤 데이터가 상을 받나</div>
<h1 class="slide__title">국민건강영양조사 2차 분석만으로는<br>부족합니다</h1>
<div class="slide__body">
  <table class="tbl tbl--tight">
    <thead><tr><th>데이터</th><th>강점</th><th>약점</th><th>수상 전략</th></tr></thead>
    <tbody>
      <tr><td>원내 후향 코호트</td><td>우리 기관만의 데이터</td><td>선택 편향·결측</td><td>코호트 구축 자체를 기여로</td></tr>
      <tr><td>공개 데이터셋</td><td>재현·벤치마크</td><td>외부 타당도</td><td>방법론 + 외부 검증 계획</td></tr>
      <tr><td>국민건강영양조사</td><td>전국 대표성</td><td>독창성 약함</td><td>정책·추세 + 다른 자료 연결</td></tr>
    </tbody>
  </table>
  <p class="lede-sm">올해 수상 사례: 검진센터 <em>H. pylori</em> 후향 코호트, 그리고 공개 데이터셋 연구(제 연구).</p>
</div>
""", label="데이터전략")

# 17 closing
add("마무리", """
<div class="slide__kicker">오늘 저녁, 세 가지</div>
<h1 class="slide__title">완주가 아니라<br>첫 표 하나가 목표입니다</h1>
<div class="slide__body">
  <ol class="actions">
    <li><b>01</b><span>OpenCode를 설치하고 폴더 하나를 연다</span></li>
    <li><b>02</b><span><code>@academic-research-writing</code>을 불러 본다</span></li>
    <li><b>03</b><span>내 초록을 넣고 “문제 3개만 짚어줘”라고 한다</span></li>
  </ol>
  <p class="closing-line">감사합니다. 질문은 지금 받겠습니다.</p>
</div>
<div class="slide__source">github.com/kimhs950627/ai-research-copilot · guide/index.html</div>
""", label="마무리")


def build():
    for i, s in enumerate(SLIDES, 1):
        body = s["body"] + footer(i, s["label"])
        page = HEAD.format(title=s["title"], idx=f"{i:02d}", cls=s["cls"], body=body)
        (OUT / f"{i:02d}.html").write_text(page, encoding="utf-8")

    # print version — all slides stacked, 16:9 pages
    parts = []
    for i, s in enumerate(SLIDES, 1):
        body = s["body"] + footer(i, s["label"])
        parts.append(f'<section class="slide {s["cls"]}" data-index="{i:02d}">{body}</section>')
    print_html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>AI와 함께 논문 쓰고 발표하기 — 인쇄용</title>
<link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="deck.css">
<style>@page{{size:13.333in 7.5in;margin:0}} body{{margin:0;background:#fff}}
.slide{{page-break-after:always;break-after:page}}</style></head>
<body>{''.join(parts)}</body></html>"""
    (HERE / "deck-print.html").write_text(print_html, encoding="utf-8")

    # presentation shell
    shell = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>AI와 함께 논문 쓰고 발표하기</title>
<style>
  html,body{margin:0;height:100%;background:#0F171C;overflow:hidden;font-family:"Pretendard","Noto Sans KR",sans-serif}
  #stage{position:absolute;inset:0;display:grid;place-items:center}
  #frame{position:absolute;left:50%;top:50%;width:1920px;height:1080px;border:0;transform-origin:center center;background:#F6F8F9}
  #hud{position:fixed;left:20px;bottom:16px;color:#F6F8F9;font-size:14px;letter-spacing:.08em;opacity:.65}
  #hud b{color:#7FC8D8}
  #help{position:fixed;right:20px;bottom:16px;color:#F6F8F9;font-size:13px;opacity:.45}
  @media print{#hud,#help{display:none}}
</style></head>
<body>
<div id="stage"><iframe id="frame" src="slides/01.html" title="슬라이드"></iframe></div>
<div id="hud"><b id="cur">01</b> / 17</div>
<div id="help">← → 이동 · F 전체화면</div>
<script>
const N=17; let i=1;
const f=document.getElementById('frame'), cur=document.getElementById('cur');
function fit(){
  const s=Math.min(innerWidth/1920, innerHeight/1080);
  f.style.transform='translate(-50%,-50%) scale('+s+')';
}
function go(n){ i=Math.max(1,Math.min(N,n)); f.src='slides/'+String(i).padStart(2,'0')+'.html'; cur.textContent=String(i).padStart(2,'0'); }
addEventListener('resize',fit); fit();
addEventListener('keydown',e=>{
  if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(i+1)}
  if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(i-1)}
  if(e.key==='Home')go(1); if(e.key==='End')go(N);
  if(e.key==='f'||e.key==='F'){document.documentElement.requestFullscreen?.()}
});
addEventListener('click',e=>{ if(e.clientX>innerWidth*0.7) go(i+1); else if(e.clientX<innerWidth*0.3) go(i-1); });
</script></body></html>"""
    (HERE / "index.html").write_text(shell, encoding="utf-8")
    print(f"built {len(SLIDES)} slides → {OUT}")

if __name__ == "__main__":
    build()
