# script-to-cuecards — 대본 → 인쇄용 큐카드 PDF

발표·사회 대본(MD/TXT/DOCX)을 **A4 세로 한 장에 두 장**씩 붙는 지참용 큐카드 PDF로 바꿈.
가운데 점선을 따라 잘라 번호순으로 쌓으면 끝임.

## 구성

| 파일 | 하는 일 |
|---|---|
| `SKILL.md` | 에이전트용 사용 지침·트리거 |
| `scripts/make_cuecards.py` | 파싱 + 인쇄 HTML 생성 + 헤드리스 Chrome 렌더 + 내장 검증 |
| `scripts/check_cuecards.py` | 만들어진 PDF 독립 검증(기하·번호·원문 무손실) |
| `assets/cuecards.css` | 판형·토큰 (덱의 `tokens_v3.css` 에서 상속) |
| `assets/paginate.js` | 페이지 안에서 실측 높이로 카드를 채우는 스크립트 |
| `examples/sample_script.md` | 블록 종류를 모두 쓰는 예시 대본 |
| `references/design-and-print.md` | 판형 근거·채우기 알고리즘·충전율 읽기·인쇄 |

## 쓰는 법

```bash
pip install pypdf            # 선택: 빈 페이지 정리·검증에만 씀 (없어도 렌더는 됨)
python3 scripts/make_cuecards.py -i examples/sample_script.md -o cuecards.pdf --title "발표 리허설"
python3 scripts/check_cuecards.py cuecards.pdf --source examples/sample_script.md
```

한 대본을 지참용/참고용으로 나눌 때:

```bash
python3 scripts/make_cuecards.py -i 발표대본.md -o 큐카드_발표.pdf   --part 발표 --skip-front --title "발표 · 큐카드"
python3 scripts/make_cuecards.py -i 발표대본.md -o 큐카드_질의응답.pdf --part 토론 --part 예상 --title "질의응답 참고 카드"
```

## 대본이 카드가 되는 규칙

- `# 제목` → part(덱 이름, 카드 푸터에 표시)
- `## 6. SupCon은 … — 60초` → **카드 한 장**(§번호와 `60초` 배지로 분리해 표시)
- `### 소제목`, `- 불릿`, `1. 번호`, `| 표 |` → 블록(각각 독립적으로 카드가 넘어감)
- `> 무대: …` → 스테이지 지시(베이지 블록, 낭독 대상 아님) / 그 밖의 `>` 는 인용 블록
- `[청중 보기]` → 큐 칩,  `---` → 여기서 강제로 카드 나눔
- 원문은 **요약·윤문·생략하지 않음**. 한 카드에 안 들어가면 같은 제목 + "계속" 카드로 이어짐.

## 의존성·제약

- Python 3.9+ (표준 라이브러리만). `pypdf` 선택, DOCX 는 `python-docx` 필요.
- 렌더 엔진은 **로컬 Chrome/Edge**(Windows Chrome 우선 — 한글 폰트와 A4 실측이 정확함).
  없으면 `--chrome` 또는 `CUECARD_CHROME` 로 지정함. 네트워크는 쓰지 않음.
- 대본·폰트·PDF 는 외부로 전송하지 않음.
- 표는 표 레이아웃이 아니라 행 한 줄 = 블록으로 바뀜. 표 모양을 그대로 옮기려면 `book-craft`.

## 인쇄

A4 세로 / 실제 크기 100 % / **단면** / "한 면에 1페이지" → 가운데 점선을 자름.
프린터의 "한 면에 2페이지" 옵션은 쓰지 않음(이미 두 장이 들어 있음).
