# 발표자료 — AI와 함께 논문 쓰고 발표하기

17장, 16:9 (1920×1080). 약 20분 발표용.

- `index.html` — 발표용. 브라우저에서 열고 `←` `→`로 이동, `F` 전체화면.
- `deck.pdf` — 발표장 백업용. **실제 발표는 이 PDF를 권장합니다.**
- `slides/NN.html` — 슬라이드 1장씩. 인쇄·검사용.
- `deck-print.html` — 16:9 페이지로 인쇄할 때.
- `build_deck.py` — 내용을 고치고 다시 만들 때: `python3 build_deck.py`
- `tokens.css`, `deck.css` — 색·타이포. 토큰만 고치면 전체 톤이 바뀝니다.

## 다시 만들기

```bash
python3 build_deck.py
# 검사 (deck-craft 스킬이 설치되어 있을 때)
~/.config/opencode/skills/deck-craft/scripts/deck-check.sh .
```

## 발표 팁

- 발표장 PC에 폰트가 없으면 HTML이 달라집니다. **PDF로 발표하세요.**
- 슬라이드에는 숫자를 최소로. 말로 설명하고, 숫자는 표에 둡니다.
- 17장을 20분에 말하면 슬라이드당 약 70초입니다. 급하면 14–16장을 줄이세요.
