# Numbering pass — reference · table · figure

Read this when `numbering_audit.py` reports something, or when the manuscript must pass a
journal's own numbering conventions.

## The contract

Three separate numberings, each with one invariant:

1. **References** — numbered by **first appearance**, every bracket resolves, no gaps.
2. **Tables** — `Table 1..N` in order of **first in-text citation**, every table cited, every
   citation defined.
3. **Figures** — same rule, independent sequence from tables.

Supplementary items get their own `S` prefix (`Table S1`, `Figure S2`) and a separate sequence.
Never mix: `Table 2` after `Table S1` means the reader cannot tell which list to open.

## What the script catches

| Finding | Severity | Meaning |
|---|---|---|
| 정의되었으나 인용 없음 | HIGH | 캡션은 있는데 본문이 가리키지 않음 — 심사자가 "왜 있는 표인가"를 묻는다 |
| 인용되었으나 정의 없음 | HIGH | 본문이 없는 표/그림을 가리킴 — 가장 흔한 투고 반려 사유 |
| 캡션 중복 | MED | 같은 번호의 캡션이 두 번 |
| 번호 결번 | MED | 1, 3, 4 — 2가 사라짐 |
| 첫 인용 순서 위반 | MED | Table 2가 Table 1보다 먼저 등장 |
| 참고문헌 순서 불일치 | MED | [2]가 [1]보다 먼저 인용됨 |

## What the script cannot catch — check by eye

1. **Placement.** 인용은 그 항목을 **논의하는 문단 안**, 첫 언급 직후에 온다. 절 끝이나
   문단 끝에 몰아넣은 인용은 위치 오류다. 표는 첫 인용 문단 다음 페이지가 원칙.
2. **Caption self-containment.** 캡션만 읽고 이해되어야 한다: 대상(n), 통계 종류, 단위,
   약어 정의, 검정 방법. 본문을 읽어야 이해되는 캡션은 MED.
3. **Consistency across files.** 논문의 `Table 1`과 표 모음 파일의 첫 표가 **같은 표**여야
   한다. 표 모음이 번호 없이 파일명(`table_baseline.xlsx`)으로만 되어 있으면, 매핑표를 만들어
   리포트에 붙인다 — 이것이 없으면 번호 감사는 절반만 된 것이다.
4. **Figure panel labels.** `Figure 1A`와 `Figure 1a`, `Fig. 1`과 `Figure 1`이 섞이면 통일.
   패널은 `A, B, C` 대문자, 캡션에서 패널별로 한 줄씩 설명.
5. **Reference content.** `[7]`이 실제로 그 논문을 가리키는지는 이 스킬의 범위 밖이다 →
   `academic-research-writing`의 인용 검증으로 넘긴다. 여기서는 **번호와 위치**만 본다.
6. **Deck–paper number agreement.** 슬라이드의 "Table 2"가 논문의 Table 2와 같아야 한다.
   발표자료는 번호를 새로 매기는 경우가 많아 여기서 자주 어긋난다 → HIGH.

## Common breakages and the fix

- **표를 나중에 추가해 번호가 밀림** — 표를 하나 넣으면 이후 번호가 전부 밀린다. 고칠 때는
  본문 인용 → 캡션 → 표 모음 → 덱 순서로 한 번에 훑는다. 한 파일만 고치면 반드시 어긋난다.
- **보충자료를 본문 번호에 섞음** — `Table 3`(보충)을 본문 `Table 2` 뒤에 두면 독자는 본문에
  표가 3개 있다고 읽는다. `Table S1`로 분리.
- **그림을 "아래 그림"으로 지칭** — 번호가 없으면 인쇄 후 위치가 바뀌며 의미가 깨진다.
  모든 지칭은 번호로.
- **캡션과 본문 수치 불일치** — 캡션의 n과 본문의 n이 다르면 HIGH. 스크립트는 못 잡는다,
  표 모음과 본문을 나란히 놓고 n·단위·검정을 대조한다.

## Output for the report

번호 관련 지적은 **한 묶음**으로 낸다. 개별 산발 지적은 저자가 고칠 수 없다.

```
[NUMBERING] 표 3건 / 그림 2건 / 참고문헌 1건
- [HIGH] Figure 2: 본문 L214에서 인용, 캡션 없음 (그림 모음에는 F2가 있으나 번호 미기재)
- [HIGH] Table 2: 캡션은 있으나 본문 인용 없음 — Results L188 뒤에 인용 문장 필요
- [MED]  Table 1이 Table 2보다 늦게 첫 인용됨 (L201 vs L188) — 순서 교체 또는 재번호
- [MED]  참고문헌 [3]이 [2]보다 먼저 인용됨 (L44 vs L61)
```
