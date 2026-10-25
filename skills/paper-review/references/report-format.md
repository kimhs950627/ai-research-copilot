# Report format

Read this when writing the final report. The report is the artifact the author works from, so its
shape decides whether anything gets fixed.

## Shape

No wide tables (Discord and mobile do not render them, and a table of findings hides the ranking).
Numbered list, grouped by severity, and inside a group ordered by where in the paper it appears.

```
## 판정 요약 (3줄)
- HIGH 5 / MED 7 / LOW 4
- 결정을 바꾸는 것은 3건: 초록의 인과 주장, Figure 2 미정의, 덱의 OR 불일치
- 검토 범위: paper.md 1,240단어, 표 4, 그림 3, 덱 14장 · 미검토: 통계 재계산, 인용 실재성

## HIGH
1. …
2. …

## MED
…

## LOW
…

## 확인하지 못한 것
- …
```

## Each finding — three lines, never more

```
1. [HIGH] paper.md L142 — 초록이 "independent predictor"라고 하지만 Results는 조정 없는
   단변량 OR만 제시한다.
   왜: 심사자가 가장 먼저 잡는 불일치이고, 근거 문장이 원고에 없다.
   제안: 조정 모형을 Results에 추가하거나, 초록을 "was associated with"로 내린다.
```

- **위치** — 파일 + 줄 번호. 줄 번호가 없으면 절 이름 + 인용문 첫 5단어.
- **왜** — 심사자가 그것을 문제로 삼는 이유. "AI 같아서"는 이유가 아니다.
- **제안** — 저자가 실행할 수 있는 동작 하나. "톤을 부드럽게"는 제안이 아니다.

## Severity rules

- **HIGH** — 이 상태로 투고하면 반려 또는 major revision. 근거 없는 초록 주장, 정의 없는
  그림 인용, 덱과 논문의 수치 불일치, 설계가 지지하지 않는 인과 주장.
- **MED** — 고치면 논문이 분명히 좋아지고 한 시간 안에 가능. 숫자 나열, 번호 순서, AI 티 문단,
  과잉 hedge, 캡션 자기완결성.
- **LOW** — 다듬기. 접속어 반복, 긴 문장, 캡션 표현.

HIGH가 10건을 넘으면 심각도가 아니라 **목록이 잘못된 것**이다. 그때는 상위 3건만 HIGH로 남기고
나머지를 MED로 내린 뒤, "이 3건이 결정을 바꾼다"고 명시한다.

## What to always state

1. **검토 범위** — 어떤 파일을, 몇 단어, 어떤 패스로 봤는지. 스크립트를 못 돌렸으면 그 사실.
2. **미검토 항목** — 통계 재계산, 인용 실재성, 저널 규정 준수, 윤리 서류. 침묵하면 검토한
   것으로 읽힌다.
3. **유지한 지적** — 스크립트가 플래그했지만 과학적으로 맞아 남긴 항목과 그 이유. 오탐을
   조용히 지우면 다음 실행에서 같은 줄이 다시 뜬다.
4. **결정 3건** — 심사자가 실제로 지적할 상위 3개. 저자가 시간이 없으면 이것만 고친다.

## Never

- 없는 분석·인용·저널 규칙을 지어내지 않는다. 원고에 없으면 "명시되지 않음"이 지적이다.
- 원고를 대신 다시 쓰지 않는다. 수정 문장은 **예시 한 줄**까지, 전문 재작성은 요청받았을 때만
  (`academic-research-writing`으로 넘긴다).
- 수치를 바꾸는 수정을 제안하지 않는다. 수치가 틀렸다고 판단되면 "원자료와 대조 필요"로 남긴다.
- 기밀 원고를 gist·외부 URL에 올리지 않는다. 리포트는 로컬 파일로.
