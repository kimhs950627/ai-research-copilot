# AI Research Copilot — Windows 설치

이 스크립트는 저장소의 `skills` 폴더를 OpenCode가 읽는 위치로 복사합니다.
관리자 권한은 필요 없습니다.

## 실행

저장소 폴더에서 PowerShell을 열고:

```powershell
powershell -ExecutionPolicy Bypass -File .\install\install-windows.ps1
```

- 대상 경로: `%USERPROFILE%\.config\opencode\skills`
- 이미 같은 이름의 스킬이 있으면 **덮어쓸지 물어봅니다**.
- `-Force`를 붙이면 묻지 않고 덮어씁니다.
- `-DryRun`을 붙이면 무엇을 복사할지 먼저 보여 줍니다.

## 설치 확인

OpenCode를 완전히 종료했다가 다시 실행하고, 대화창에 `@academic`을 입력했을 때
자동완성 목록에 `academic-research-writing`이 뜨면 성공입니다.

## 수동 설치

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.config\opencode\skills" | Out-Null
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.config\opencode\skills\"
```

## 되돌리기

복사한 스킬 폴더만 지우면 됩니다.

```powershell
Remove-Item -Recurse "$env:USERPROFILE\.config\opencode\skills\academic-research-writing"
```
