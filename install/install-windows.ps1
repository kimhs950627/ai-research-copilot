# AI Research Copilot — Windows 설치 스크립트
# 사용법:
#   powershell -ExecutionPolicy Bypass -File .\install\install-windows.ps1
#   powershell -ExecutionPolicy Bypass -File .\install\install-windows.ps1 -DryRun
#   powershell -ExecutionPolicy Bypass -File .\install\install-windows.ps1 -Force

param(
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot "skills"
$dest = Join-Path $env:USERPROFILE ".config\opencode\skills"

if (-not (Test-Path $source)) {
    Write-Error "skills 폴더를 찾을 수 없습니다: $source"
    exit 1
}

Write-Host ""
Write-Host "  AI Research Copilot — 스킬 설치" -ForegroundColor Green
Write-Host "  원본: $source"
Write-Host "  대상: $dest"
Write-Host ""

$skills = Get-ChildItem -Path $source -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName "SKILL.md")
}

if ($skills.Count -eq 0) {
    Write-Error "설치할 스킬(SKILL.md가 있는 폴더)을 찾지 못했습니다."
    exit 1
}

Write-Host "  설치할 스킬 $($skills.Count)개:"
foreach ($s in $skills) { Write-Host "   - $($s.Name)" }
Write-Host ""

if ($DryRun) {
    Write-Host "  -DryRun: 아무것도 복사하지 않았습니다." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $dest)) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Write-Host "  폴더를 만들었습니다: $dest" -ForegroundColor DarkGray
}

$copied = 0
$skipped = 0

foreach ($s in $skills) {
    $target = Join-Path $dest $s.Name
    if ((Test-Path $target) -and (-not $Force)) {
        $answer = Read-Host "  '$($s.Name)'이(가) 이미 있습니다. 덮어쓸까요? (y/N)"
        if ($answer -notin @("y", "Y", "yes", "YES")) {
            Write-Host "   건너뜀: $($s.Name)" -ForegroundColor DarkYellow
            $skipped++
            continue
        }
        Remove-Item -Recurse -Force $target
    }
    Copy-Item -Recurse -Force $s.FullName $target
    Write-Host "   복사됨: $($s.Name)" -ForegroundColor Green
    $copied++
}

Write-Host ""
Write-Host "  완료 — 복사 $copied개, 건너뜀 $skipped개" -ForegroundColor Green
Write-Host ""
Write-Host "  다음 단계:"
Write-Host "   1) OpenCode를 완전히 종료했다가 다시 실행"
Write-Host "   2) 대화창에 @academic 입력 → academic-research-writing 확인"
Write-Host "   3) 논문 폴더를 열고 첫 프롬프트 실행 (guide/index.html 01장)"
Write-Host ""
