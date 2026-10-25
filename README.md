# AI Research Copilot — 의사를 위한 논문·발표 워크플로

국민건강영양조사(KNHANES) 같은 **표 형식 데이터**로 논문을 쓰고 학회에서 발표하는 일을,
AI 에이전트(OpenCode)와 **역할을 나눠** 진행하는 방법을 담은 저장소입니다.

2026년 대한가정의학회 추계학술대회에서 발표한 실제 사례(HCC vs 혈관종, 공개 초음파 데이터셋)를
바탕으로, 이미지가 아닌 **표 데이터 연구에 그대로 적용되는 절차**로 다시 썼습니다.

> **핵심 원칙** — AI에게 논문을 써 달라고 하지 마세요. AI에게 연구를 **검증하게** 하세요.

## 5분 안에 시작

1. **OpenCode 설치** — [Windows](https://opencode.ai/update/api/latest/desktop/opencode/opencode-desktop-win-x64.exe) ·
   [macOS Apple silicon](https://opencode.ai/update/api/latest/desktop/opencode/opencode-desktop-mac-arm64.dmg) ·
   [macOS Intel](https://opencode.ai/update/api/latest/desktop/opencode/opencode-desktop-mac-x64.dmg) ·
   [공식 문서](https://opencode.ai/v2/docs/)
2. **이 저장소 받기** — GitHub에서 **Code → Download ZIP** → 압축 해제 (Git 없어도 됩니다)
3. **스킬 설치** — 저장소 폴더에서 아래 실행

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\install\install-windows.ps1
```

```bash
# macOS / Linux
bash ./install/install-mac.sh
```

4. OpenCode를 다시 켜고, 논문 폴더를 연 뒤:

```
@academic-research-writing
이 폴더의 초록을 읽고, 연구 질문이 한 문장으로 명확한지 검토해줘.
고치지는 말고 문제 3개만 짚어줘.
```

## 읽을 것

| 파일 | 내용 |
|---|---|
| [`guide/index.html`](guide/index.html) · [`guide.pdf`](guide/guide.pdf) | **종합 안내서** (42쪽) — 설치, 8단계 워크플로, KNHANES 특별편, 심사 대비 전략, 프롬프트 15개 |
| [`deck/index.html`](deck/index.html) · [`deck.pdf`](deck/deck.pdf) | 동료에게 이 방법을 소개하는 **발표자료** 17장 (16:9) |
| [`script/발표대본.md`](script/발표대본.md) · [`발표대본.pdf`](script/발표대본.pdf) | 발표 대본 (약 19분) + 예상 질문 10개 |
| [`cuecards/`](cuecards/) | 인쇄용 큐카드 — 발표 23장, Q&A 10장 (A4 2분할) |
| [`skills/`](skills/) | 스킬 7종 — OpenCode가 읽는 업무 매뉴얼 |
| [`guide/knhanes-weights.md`](guide/knhanes-weights.md) · [`PDF`](guide/knhanes-weights.pdf) | **2024년 가중치 정리** — 10종 변수, 선택 규칙, R/Stata 코드, 통합 |
| [`install/AGENTS.example.md`](install/AGENTS.example.md) | 내 프로필·규칙을 AI에게 알려 주는 파일 |

## 스킬 7종

| 스킬 | 언제 |
|---|---|
| `@academic-research-writing` | 문헌고찰, 원고 IMRaD, 근거 장부, 인용 검증 |
| `@deep-research` | 배경 조사, 가이드라인 비교, 팩트체크 |
| `@paper-review` | 투고 전·발표 전 자체 심사 |
| `@design-craft` | 보고서·포스터·슬라이드의 색·타이포·여백 |
| `@deck-craft` | 16:9 발표자료(HTML·PPTX·PDF)와 발표자 노트 |
| `@script-to-cuecards` | 대본 → 인쇄용 큐카드 |
| `@clinical-prescribing-safety` | 처방·용량·금기·상호작용 (결정 지원, 서명은 사람) |

## 국민건강영양조사를 쓴다면

이 저장소의 예시는 이미지 연구지만, 절차는 동일합니다. **딱 하나 더** 지켜야 합니다.

> “이 분석은 복합표본설계입니다. 층(`kstrata`)·집락(`psu`)·가중치(`wt_*`)를 반영하고,
> 변수명은 코드북에서 확인한 뒤 주석에 적으세요. 가중치를 빼면 결과를 폐기하겠습니다.”

자세한 내용은 안내서 **06 / KNHANES** 장을 보세요.

## 저장소 구조

```
ai-research-copilot/
├─ guide/          종합 안내서 (HTML + PDF)
├─ deck/           소개 발표자료 (HTML + PDF)
├─ script/         발표 대본
├─ cuecards/       인쇄용 큐카드
├─ skills/         스킬 7종
├─ install/        Windows·macOS 설치 스크립트, AGENTS 예시
├─ examples/       KNHANES 연습 폴더, 사례 요약
└─ design/         디자인 토큰 (테마 근거)
```

## 라이선스

- 이 저장소의 글·그림·발표자료: **CC BY 4.0** (출처를 밝히면 자유롭게 사용)
- 스킬 코드: 각 스킬 폴더의 라이선스 표기
- 인용한 논문·데이터: 원저작자

## 주의

이 저장소는 교육 목적의 안내서이며, 특정 환자의 진단·치료를 대신하지 않습니다.
AI가 만든 초안과 숫자는 **반드시 사람이 원자료로 확인하고 서명**해야 합니다.
환자 개인정보가 포함된 파일은 어떤 채팅에도 올리지 마세요.
