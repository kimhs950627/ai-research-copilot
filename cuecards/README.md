# 큐카드 — 인쇄용

- `큐카드_발표.pdf` — 발표 17구간, 23카드 / A4 12장
- `큐카드_질의응답.pdf` — 예상 질문 10개 / A4 5장

## 인쇄 방법

1. A4 세로
2. **실제 크기 100%** (PDF에 이미 2분할이 들어 있습니다)
3. **단면**, 프린터의 “한 면에 2페이지” 기능은 끄기
4. 가운데 점선을 자르고 카드 번호 순서로 쌓기

## 다시 만들기

대본을 고친 뒤:

```bash
S=~/.config/opencode/skills/script-to-cuecards/scripts
python3 $S/make_cuecards.py -i ../script/발표대본.md -o 큐카드_발표.pdf \
  --part 발표 --skip-front --title "AI와 함께 논문 쓰고 발표하기 · 큐카드"
python3 $S/make_cuecards.py -i ../script/발표대본.md -o 큐카드_질의응답.pdf \
  --part 예상 --skip-front --title "AI 논문·발표 가이드 · 질의응답 카드"
```
