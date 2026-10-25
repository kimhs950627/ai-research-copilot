#!/usr/bin/env bash
# AI Research Copilot — macOS / Linux 설치
# 사용법:
#   bash ./install/install-mac.sh
#   bash ./install/install-mac.sh --dry-run
#   bash ./install/install-mac.sh --force

set -euo pipefail

FORCE=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --dry-run) DRY=1 ;;
    *) echo "알 수 없는 옵션: $arg"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/skills"
DEST="$HOME/.config/opencode/skills"

if [ ! -d "$SRC" ]; then
  echo "skills 폴더를 찾을 수 없습니다: $SRC" >&2
  exit 1
fi

echo
echo "  AI Research Copilot — 스킬 설치"
echo "  원본: $SRC"
echo "  대상: $DEST"
echo

mapfile -t SKILLS < <(find "$SRC" -mindepth 1 -maxdepth 1 -type d -exec test -f '{}/SKILL.md' \; -print | sort)

if [ ${#SKILLS[@]} -eq 0 ]; then
  echo "설치할 스킬(SKILL.md가 있는 폴더)을 찾지 못했습니다." >&2
  exit 1
fi

echo "  설치할 스킬 ${#SKILLS[@]}개:"
for s in "${SKILLS[@]}"; do echo "   - $(basename "$s")"; done
echo

if [ "$DRY" -eq 1 ]; then
  echo "  --dry-run: 아무것도 복사하지 않았습니다."
  exit 0
fi

mkdir -p "$DEST"

copied=0
skipped=0
for s in "${SKILLS[@]}"; do
  name="$(basename "$s")"
  target="$DEST/$name"
  if [ -e "$target" ] && [ "$FORCE" -eq 0 ]; then
    read -r -p "  '$name'이(가) 이미 있습니다. 덮어쓸까요? (y/N) " answer
    case "$answer" in
      y|Y|yes|YES) ;;
      *) echo "   건너뜀: $name"; skipped=$((skipped+1)); continue ;;
    esac
    rm -rf "$target"
  fi
  cp -R "$s" "$target"
  echo "   복사됨: $name"
  copied=$((copied+1))
done

echo
echo "  완료 — 복사 $copied개, 건너뜀 $skipped개"
echo
echo "  다음 단계:"
echo "   1) OpenCode를 완전히 종료했다가 다시 실행"
echo "   2) 대화창에 @academic 입력 → academic-research-writing 확인"
echo "   3) 논문 폴더를 열고 첫 프롬프트 실행 (guide/index.html 01장)"
echo
