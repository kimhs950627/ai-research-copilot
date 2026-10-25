---
name: script-to-cuecards
description: >
  Turn a speaking script (MD/TXT/DOCX) into printable speaker cue cards: portrait A4 with two
  148.3 mm cards per sheet, a dashed cut line, per-card numbering, section badges with timing,
  muted stage directions, and text that continues on the next card instead of being shrunk —
  rendered to PDF by the browser print engine (no LaTeX, no pip install). Use when 큐카드, 인쇄용 발표 대본,
  사회자·진행자·아나운서 대본 카드, 발표 리허설 카드. KO: 큐 카드, 대본 카드, 대본을 카드로, 발표 대본 인쇄, 사회자 대본, 진행자 대본, 아나운서 대본, 지참
  카드, 발표 리허설, 진행 대본 카드, speech note cards, cue cards.
---

# script-to-cuecards

대본 한 편 → 손에 들고 보는 인쇄용 큐카드 PDF. A4 세로 한 장에 카드 두 장, 중앙 점선 재단선.

```
대본 .md/.txt/.docx
      │  parse  → 블록(문단·불릿·표행·무대지시·인용) + part/section
      ▼
인쇄 HTML (assets/cuecards.css)  ──  assets/paginate.js 가 실측 높이로 카드를 채움
      ▼
헤드리스 Chrome --print-to-pdf  →  PDF  →  내장 self-check (기하 + 텍스트 무손실)
```

판형·토큰·검증 방식의 근거는 `references/design-and-print.md` 를 읽음.

## When this applies / When it does not

> **제시 전 디자인 검토 (design-craft Rule −1)** — 인쇄 PDF 는 시각 산출물이므로 **사용자에게 넘기기
> 전에** ① `theme-advisor.py --medium cuecard` 로 테마를 뽑아 `--report` 대비 PASS 를 확인하고(대본마다
> 같은 큐카드가 나오지 않게 함) ② `make_cuecards.py` 자체 검증(exit 3)에 더해 A4 기하·페이지 채움·
> 한글 어절 쪼개짐·마크다운 누출을 확인하고 ③ 렌더 PNG 1장(첫 페이지)을 `kimaki upload-to-discord` 로
> 올린다. 검사 결과와 `테마: <theme> · 대비 PASS` 한 줄, 그리고 비전 판정 불가 사실을 밝힌다.

- Use for: 대본을 **지참·낭독용 카드**로 인쇄. 발표 대본, 사회자·진행자 대본, 아나운서 원고,
  리허설 카드, Q&A 참고 카드. 입력은 이미 쓰여진 대본 파일.
- Do not use for: **슬라이드 자체**를 만들 때 → `deck-craft`; A4 여러 장짜리 보고서·책 →
  `book-craft`; 정사각 SNS 카드뉴스 → `card-craft`; 대본을 처음부터 새로 쓸 때 → 그냥 쓰면 됨
  (이 스킬은 원문을 요약·윤문하지 않음).

## Workflow

1. **대본 경로를 확인**함. 파일이 없으면 업로드를 요청함. 예시 파일을 사용자 대본으로
   착각하지 않음. 대본의 part(`#`)와 section(`## N. 제목 — 45초`) 구조를 눈으로 확인함.
2. **파싱만 먼저 검사**함 — `--html-only` 로 HTML 을 뽑아 블록 종류·카드 단위를 확인함.
   표·불릿·무대지시가 의도한 블록으로 잡혔는지 여기서 봄.
3. **테마를 유도**함 (design-craft) — 색·폰트를 대본마다 새로 뽑아 큐카드가 매번 같아 보이지 않게 함.
   `theme-advisor.py --medium cuecard`(기본 `document-plain`, 낭독 리허설이면 `editorial-serif`) →
   `--report` 대비 PASS → 토큰을 `--css` 파일의 `:root` 에 덮어씀. **기하 토큰(`--pad-y`·`--card-h`·
   `--cut`)은 건드리지 않음** — 재단·A4 검증이 깨진다(`references/design-and-print.md` §2).
4. **렌더**함 (아래 기본 명령). 대본에 `# 발표 대본`, `# 토론`, `# 예상 질문과 답변` 처럼 part 가
   여럿이면 part 별로 **PDF 를 따로** 만듦 (지참용 = 발표 파트, 책상용 = 질의응답 파트).
5. **검증**함 — `make_cuecards.py` 가 스스로 A4 기하·카드 수·블록 무손실을 검사하고, 실패하면
   exit 3 으로 시끄럽게 실패함. 필요하면 `check_cuecards.py --source` 로 한 번 더 확인함.
6. **전달**함 — PDF 를 업로드하고 카드 수·페이지 수·인쇄 방법(아래)을 짧게 안내함. 실제로
   만들지 않았으면 만들었다고 말하지 않음.

## Commands

```bash
S=~/.config/opencode/skills/script-to-cuecards/scripts

# 기본: 대본 → A4 세로 2분할 큐카드 PDF
python3 $S/make_cuecards.py -i "발표대본.md" -o "큐카드.pdf" \
  --title "발표 제목 · 큐카드"

# part 별로 지참용/참고용을 나누고, 표지 메타데이터는 뺌
python3 $S/make_cuecards.py -i 발표대본.md -o 큐카드_발표.pdf  --part 발표 --skip-front --title "…"
python3 $S/make_cuecards.py -i 발표대본.md -o 큐카드_질의응답.pdf --part 토론 --part 예상 --title "…"

# 파싱 확인(렌더 전) / 페이지별 충전율 확인(렌더 후)
python3 $S/make_cuecards.py -i 발표대본.md -o x.pdf --html-only
python3 $S/make_cuecards.py -i 발표대본.md -o x.pdf --dom-report

# 독립 검증
python3 $S/check_cuecards.py 큐카드_발표.pdf --source 발표대본.md --part 발표 --skip-front
```

- `--per-page 4` = A6 크기 카드 4장(2×2), `--no-cut-line`, `--font-size 16`, `--line-height 1.5`,
  `--paragraph-gap 2.6`(mm), `--block-chars 200`, `--keep-breaks`, `--css` 로 토큰 교체.
- **테마 적용은 `--css` 로 한다**: `theme-advisor.py --medium cuecard` 로 뽑은 색·폰트를
  `assets/cuecards.css` 사본의 `:root` 에 덮어쓰고 그 파일을 넘긴다(기본 파일은 건드리지 않는다).
  기하 토큰(`--pad-y`·`--card-h`·`--cut`)은 그대로 — 바꾸면 인쇄 검증이 깨진다.
- `--part <문자열>` 는 H1(part) 제목 부분일치, 여러 번 가능. `--skip-front` 는 첫 `## ` 앞의
  표지·변경내역만 버림(part 라벨은 남김).
- 크롬 탐색: `CUECARD_CHROME` 환경변수 → `--chrome` → Windows Chrome/Edge 자동 탐색.
  Windows Chrome 이면 HTML/PDF 를 `CUECARD_WIN_TMP`(기본 `/mnt/c/Users/pc/AppData/Local/Temp`)에
  스테이징하고 결과만 출력 경로로 복사함.

## Card anatomy

```
┌──────────────────────────────────────────────────────────────┐ 210 mm
│ 발표 제목 · 큐카드(초록 eyebrow)            카드 03 / 19(회색) │
│ §6 SupCon은 임베딩의 모양을 바꾼다                 60초        │  ← §번호·제목·배분
│ ──────────────────────────────────────────────────────────── │
│ 본문 16 pt / 행간 1.5 — 원문 그대로, 줄이지 않음              │
│ • 불릿 항목                                                  │
│ ┃무대  ← 스테이지 지시(베이지 블록 + 앰버 좌측 규칙)          │
│ ──────────────────────────────────────────────────────────── │
│ 발표 대본 — v3                                     03 / 19   │
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌ 점선 재단선 148.3 mm ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
│ (아래 카드 = 같은 구조)                                       │ 148.3 mm
└──────────────────────────────────────────────────────────────┘ 296.6 mm
```

- 카드 단위 = `## N. 제목 — 45초` 1개. 넘치면 **같은 제목 + "계속"** 카드로 이어짐(글자 축소 없음).
- `#` = part(카드 하단 왼쪽에 표시), `---` = 강제 카드 나눔, `> 무대:` = 지시 블록,
  `[청중 보기]` = 큐 칩, `- 불릿` / `1. 번호` / `| 표 |` 는 각각 항목·행 단위 블록이 됨.
- 한 카드에 들어가는 분량은 16 pt/1.5 에서 대략 **350–400자**. 원문은 요약·윤문·생략하지 않음.

## 인쇄 안내 (사용자에게 이대로 전함)

- A4 세로 · 실제 크기 100 % · **단면** · "한 면에 1페이지". PDF 내부가 이미 2분할이므로
  프린터의 "한 면에 2페이지"는 쓰지 않음.
- 가운데 점선을 자르고 카드 번호순으로 쌓음. 리허설에서 넘겨 보고 순서를 확인함.

## Limits and failure modes (실제로 확인한 것)

- 시트 높이를 297 mm 로 꽉 채우면 Chrome 이 페이지를 한 장 더 나눔 → CSS 가 296.6 mm(카드
  148.3 mm ×2)로 잡고, 그래도 남는 빈 꼬리 페이지는 pypdf 로 잘라냄. 점선은 실제 중앙에서
  0.2 mm 어긋남(재단 여유).
- 카드 채우기는 페이지 안에서 **실측 렌더 높이**(`getBoundingClientRect`)로 판정함. 여백은
  넘침으로 세지 않음.
- 섹션이 반 카드보다 짧으면 그 카드는 비어 보임(충전율 20–40 % 가 몇 장 생김). 정상 동작이지만
  더 촘촘하게 원하면 `--font-size 15` 또는 대본에 `---` 로 카드를 직접 나눔.
- pypdf 가 없으면 렌더는 되지만 빈 페이지 정리와 검증이 생략됨(`pip install pypdf`).
- DOCX 는 본문 문단과 표 셀만 읽음. 머리말·꼬리말·각주·텍스트 상자·이미지·변경 추적은 변환하지
  않음 — 대본이 그 안에 있으면 본문으로 옮겨 달라고 요청함.
- 대본 안의 **이미지·도표는 인쇄하지 않음**(텍스트만). 슬라이드 그림 참조는 `[그림 3]` 같은
  큐 칩으로만 남음.
- 표는 표 레이아웃이 아니라 **행 한 줄 = 블록**으로 바꿈(`측정항목 — 값 · 값 · 비고`). 표를
  그대로 옮겨야 하는 요청이면 이 스킬이 아니라 `book-craft` 쪽이 맞음.
- 한 블록이 카드 하나보다 크면 잘림 — `--block-chars` 를 낮추거나(기본 200) `---` 로 나눔.
  내장 검증이 이 경우를 잡아 exit 3 으로 알림.

## Deep detail

- Read `references/design-and-print.md` when 판형·토큰을 바꾸거나, 충전율/카드 수를 조정하거나,
  인쇄가 이상할 때.
- `scripts/make_cuecards.py` — 파싱 + HTML + Chrome 렌더 + self-check (2026-10-18 실대본으로 검증).
- `scripts/check_cuecards.py` — PDF 단독 검증(A4 기하·카드 번호 연속·페이지 채움·원문 무손실).
- `assets/cuecards.css` (판형·토큰), `assets/paginate.js` (실측 채우기), `examples/sample_script.md`.
