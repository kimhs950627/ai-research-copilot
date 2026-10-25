# 스킬 7종 — 무엇을, 언제, 어떻게

OpenCode는 `~/.config/opencode/skills/<이름>/SKILL.md`를 읽습니다.
대화 중 `@이름`으로 직접 부르거나, 작업을 설명하면 알맞은 스킬을 스스로 고릅니다.

| 폴더 | 아이디 | 역할 | 대표 트리거 |
|---|---|---|---|
| `academic-research-writing` | `@academic-research-writing` | 문헌고찰·원고·근거 장부·인용 검증 | “논문”, “원고”, “문헌고찰”, “출처” |
| `deep-research` | `@deep-research` | 조사·비교·팩트체크 | “조사해줘”, “최신 동향”, “비교” |
| `paper-review` | `@paper-review` | 제출 전 자체 심사 | “검토”, “리뷰”, “투고 전” |
| `design-craft` | `@design-craft` | 보고서·포스터·슬라이드의 시각 설계 | “예쁘게”, “PDF”, “포스터” |
| `deck-craft` | `@deck-craft` | 16:9 발표자료 (HTML·PPTX·PDF) | “발표자료”, “슬라이드”, “PPT” |
| `script-to-cuecards` | `@script-to-cuecards` | 대본 → 인쇄용 큐카드 | “큐카드”, “대본 인쇄” |
| `clinical-prescribing-safety` | `@clinical-prescribing-safety` | 처방·용량·금기·상호작용 | “처방”, “용량”, “금기” |

## 겹칠 때의 순서

1. **환자 안전**이 걸리면 `clinical-prescribing-safety`가 먼저.
2. **내용**은 `academic-research-writing`, **표면**은 `design-craft`/`deck-craft`.
3. **조사**는 `deep-research`, **문서**는 `academic-research-writing`.
4. **발표자료**가 정해진 뒤에 **대본**, 그 다음 **큐카드**.

## 라이선스와 출처

각 스킬 폴더의 `SKILL.md`와 `LICENSE`를 확인하세요.
`design-craft`·`deck-craft`는 공개된 디자인 원칙(Anthropic frontend-design, Vercel web guidelines 등)을
참고해 이 저장소의 사용자가 직접 작성·각색한 것입니다. 원 라이선스는 각 폴더에 표기되어 있습니다.

## 수정·기여

- 기관 규칙에 맞게 문구를 고쳐 쓰세요. 특히 `AGENTS.example.md`의 프로필 부분.
- 새 프롬프트가 좋았다면 `examples/`에 추가해 주세요.
- 스킬은 **절차서**입니다. 프롬프트 한 줄을 추가하는 것보다, “무엇을 확인하고 멈출지”를 추가하는 편이 낫습니다.
