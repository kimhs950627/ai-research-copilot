# 발표 대본

- `발표대본.md` — 원본. 고칠 때는 이 파일만 고칩니다.
- `발표대본.pdf` — 인쇄·공유용.
- `print.html` — PDF를 만들기 위한 인쇄 페이지.
- `build_script_pdf.py` — 마크다운 → 인쇄 HTML.

## 다시 만들기

```bash
python3 build_script_pdf.py
# Windows Chrome으로 PDF 인쇄
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless \
  --no-pdf-header-footer --print-to-pdf=발표대본.pdf print.html
```

대본을 고친 뒤에는 **큐카드를 다시 만들어야** 합니다.

```bash
python3 ~/.config/opencode/skills/script-to-cuecards/scripts/make_cuecards.py \
  -i 발표대본.md -o ../cuecards/큐카드_발표.pdf --part 발표 --skip-front \
  --title "AI와 함께 논문 쓰고 발표하기 · 큐카드"
```
