#!/usr/bin/env python3
"""theme-advisor — 산출물 종류에 맞는 **테마 전체**(색+타이포+레이아웃+질감+밀도+모션)를 고른다.

`palette-advisor.py` 가 색만 책임진다면, 이 스크립트는 "카드뉴스인데 책과 같은 느낌"이 되는 문제를
막는다. 테마 = ⓐ 색 계열(팔레트에게 위임) ⓑ 타이포 스케일·폰트 페어 ⓒ 밀도(여백·리듬) ⓓ 형태(반경·
그림자) ⓔ 질감(종이·그레인·그리드·스캔라인) ⓕ 명암(dark/light) ⓖ 이미지 처리 ⓗ 모션 성격.

같은 무드라도 **매체가 다르면 다른 테마**가 나오고, 히스토리로 "지난번과 같은 느낌(fingerprint)"을
감지한다.

사용:
  T=~/.config/opencode/skills/design-craft/scripts/theme-advisor.py
  python3 $T --subject "미국 주식 투자레터" --medium newsletter --mood "분석적, 차분한"
  python3 $T --theme terminal-mono --medium deck --subject "딥러닝 벤치마크" --write build/tokens.css
  python3 $T --list                # 테마 12종
  python3 $T --history 8           # 최근 쓴 테마·fingerprint (반복 감지)
  python3 $T --report tokens.css   # 색 대비 + 테마 지문/타이포 단조 검사

종료 코드: 0 = PASS · 1 = FAIL · 2 = 사용 오류.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HISTORY = Path(os.environ.get("DESIGN_CRAFT_THEME_HISTORY", Path.home() / ".cache/design-craft/theme-history.jsonl"))


def _load(mod_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PA = _load("palette_advisor", HERE / "palette-advisor.py")

# ── 프리셋 ──────────────────────────────────────────────────────────────────────
# 타이포 프리셋: 폰트 페어 + 스케일. 새 폰트를 쓰는 프리셋은 font_link 를 함께 낸다(폴백 스택은 항상 있다).
TYPE = {
    "serif-editorial": dict(
        ko="세리프 편집", font_link="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700&family=Noto+Serif+KR:wght@400;600;900&display=swap",
        display='"Fraunces", "Noto Serif KR", Georgia, serif',
        body='"Noto Serif KR", "Nanum Myeongjo", Georgia, serif',
        mono='"JetBrains Mono", "D2Coding", ui-monospace, monospace',
        h="clamp(2.5rem, 5.5vw, 4.5rem)", h1="3rem", h2="2rem", h3="1.25rem",
        body_size="1.0625rem", small="0.8125rem", leading_body=1.72, leading_heading=1.15,
        tracking_display="-0.02em", tracking_body="0", note="다단 조판·괘선과 잘 맞는다"),
    "sans-swiss": dict(
        ko="", font_link="",
        display='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(3rem, 7vw, 6rem)", h1="3rem", h2="1.75rem", h3="1.125rem",
        body_size="1rem", small="0.8125rem", leading_body=1.55, leading_heading=1.06,
        tracking_display="-0.035em", tracking_body="-0.005em", single_family="굵기·자간·크기로 대비", note="좌정렬·12컬럼·큰 숫자"),
    "mono-terminal": dict(
        ko="모노 터미널", font_link="",
        display='"JetBrains Mono", "D2Coding", ui-monospace, monospace',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", "D2Coding", ui-monospace, monospace',
        h="clamp(1.9rem, 4.2vw, 3.25rem)", h1="2.25rem", h2="1.5rem", h3="1.0625rem",
        body_size="0.9375rem", small="0.8125rem", leading_body=1.62, leading_heading=1.12,
        tracking_display="-0.01em", tracking_body="0", note="표·코드·수치 라벨이 주인공"),
    "serif-classic": dict(
        ko="고전 세리프", font_link="",
        display='"Noto Serif KR", "Nanum Myeongjo", Georgia, serif',
        body='"Noto Serif KR", "Nanum Myeongjo", Georgia, serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(2.25rem, 5vw, 4rem)", h1="2.5rem", h2="1.75rem", h3="1.1875rem",
        body_size="1.09375rem", small="0.8125rem", leading_body=1.78, leading_heading=1.2,
        tracking_display="-0.01em", tracking_body="0", single_family="굵기·이탤릭 캡션으로 대비", note="캡션·각주·괘선 장식"),
    "rounded-geometric": dict(
        ko="라운드 기하", font_link="",
        display='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(2.5rem, 6vw, 5rem)", h1="2.5rem", h2="1.75rem", h3="1.1875rem",
        body_size="1.0625rem", small="0.8125rem", leading_body=1.68, leading_heading=1.1,
        tracking_display="-0.015em", tracking_body="0", single_family="굵기·도형으로 대비", note="원·삼각 도형, 두꺼운 라운드"),
    "poster-heavy": dict(
        ko="포스터 헤비", font_link="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700&display=swap",
        display='"Black Han Sans", "Pretendard", "Noto Sans KR", sans-serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(3.25rem, 9vw, 8.5rem)", h1="3.5rem", h2="2.25rem", h3="1.25rem",
        body_size="1rem", small="0.8125rem", leading_body=1.5, leading_heading=0.94,
        tracking_display="-0.04em", tracking_body="0", note="한 화면 한 문장, 초굵은 제목"),
    "warm-humanist": dict(
        ko="따뜻한 휴머니스트", font_link="",
        display='"Noto Serif KR", "Nanum Myeongjo", Georgia, serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(2.25rem, 5vw, 4rem)", h1="2.5rem", h2="1.75rem", h3="1.1875rem",
        body_size="1.0625rem", small="0.8125rem", leading_body=1.75, leading_heading=1.18,
        tracking_display="-0.015em", tracking_body="0", note="사람 냄새 나는 세리프 제목 + 편한 본문"),
    "sans-plain": dict(
        ko="실무 산세리프", font_link="",
        display='"Noto Sans KR", "Pretendard", system-ui, sans-serif',
        body='"Noto Sans KR", "Pretendard", system-ui, sans-serif',
        mono='"JetBrains Mono", "D2Coding", ui-monospace, monospace',
        h="clamp(1.75rem, 3.2vw, 2.5rem)", h1="2rem", h2="1.4rem", h3="1.0625rem",
        body_size="0.96875rem", small="0.8125rem", leading_body=1.62, leading_heading=1.2,
        tracking_display="-0.01em", tracking_body="0", single_family="크기·번호로 대비", note="장식 0, 번호·표 중심, 흑백 인쇄 안전"),
    "sans-airy": dict(
        ko="여백 산세리프", font_link="",
        display='"Noto Serif KR", Georgia, serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", ui-monospace, monospace',
        h="clamp(2.25rem, 4.5vw, 3.75rem)", h1="2.25rem", h2="1.5rem", h3="1.0625rem",
        body_size="1.0625rem", small="0.84375rem", leading_body=1.8, leading_heading=1.24,
        tracking_display="-0.012em", tracking_body="0.002em", note="화면당 메시지 1개, 큰 여백, 작은 캡션"),
    "sans-technical": dict(
        ko="기술 산세리프", font_link="",
        display='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        body='"Pretendard", "Noto Sans KR", system-ui, sans-serif',
        mono='"JetBrains Mono", "D2Coding", ui-monospace, monospace',
        h="clamp(2rem, 3.8vw, 2.875rem)", h1="2.25rem", h2="1.5rem", h3="1.0625rem",
        body_size="0.9375rem", small="0.8125rem", leading_body=1.6, leading_heading=1.14,
        tracking_display="-0.02em", tracking_body="0", single_family="모노 라벨·크기로 대비", note="모노 라벨 + 도식·표 주석"),
}

DENSITY = {
    "airy": dict(ko="여유", space_base="8px", space_4="24px", space_12="72px", space_24="160px",
                 section_y="clamp(96px, 12vw, 180px)", section_y_lg="clamp(140px, 16vw, 260px)",
                 container_max="1040px", pad_x="clamp(32px, 7vw, 112px)"),
    "regular": dict(ko="보통", space_base="4px", space_4="16px", space_12="48px", space_24="96px",
                    section_y="clamp(64px, 8vw, 128px)", section_y_lg="clamp(96px, 12vw, 200px)",
                    container_max="1120px", pad_x="clamp(28px, 5vw, 80px)"),
    "dense": dict(ko="촘촘", space_base="4px", space_4="14px", space_12="40px", space_24="72px",
                  section_y="clamp(40px, 5vw, 80px)", section_y_lg="clamp(64px, 8vw, 120px)",
                  container_max="1200px", pad_x="clamp(24px, 4vw, 56px)"),
    "compressed": dict(ko="압축", space_base="2px", space_4="10px", space_12="28px", space_24="48px",
                       section_y="clamp(28px, 3.5vw, 56px)", section_y_lg="clamp(44px, 5vw, 88px)",
                       container_max="1320px", pad_x="clamp(20px, 3vw, 44px)"),
}

SHAPE = {
    "rule-only": dict(ko="괘선만", radius_sm="0px", radius_md="0px", radius_pill="999px",
                      border="1px solid var(--color-border)", border_strong="2px solid var(--color-border-strong)",
                      shadow_lift="none", shadow_overlay="0 24px 60px -24px rgba(0,0,0,.35)"),
    "hard": dict(ko="각진 경계", radius_sm="0px", radius_md="0px", radius_pill="0px",
                 border="2px solid var(--color-text-1)", border_strong="4px solid var(--color-text-1)",
                 shadow_lift="none", shadow_overlay="8px 8px 0 0 var(--color-text-1)"),
    "hairline": dict(ko="헤어라인", radius_sm="2px", radius_md="6px", radius_pill="999px",
                     border="1px solid var(--color-border)", border_strong="1px solid var(--color-border-strong)",
                     shadow_lift="0 1px 2px rgba(0,0,0,.06)", shadow_overlay="0 24px 60px -20px rgba(0,0,0,.28)"),
    "soft": dict(ko="부드러운 면", radius_sm="6px", radius_md="16px", radius_pill="999px",
                 border="1px solid var(--color-border)", border_strong="1px solid var(--color-border-strong)",
                 shadow_lift="0 2px 6px rgba(0,0,0,.07)", shadow_overlay="0 30px 70px -24px rgba(0,0,0,.30)"),
}

TEXTURE = {
    "flat": dict(ko="평면", texture="none", bg_extra="none"),
    "paper": dict(ko="종이", texture="grain(.035)", bg_extra="radial-gradient(120% 90% at 50% 0%, rgba(255,255,255,.5), transparent 70%)"),
    "grain": dict(ko="그레인", texture="grain(.06)", bg_extra="none"),
    "blueprint-grid": dict(ko="설계 그리드", texture="grid(1px, 96px)", bg_extra="none"),
    "scanlines": dict(ko="스캔라인", texture="scanlines(3px, .04)", bg_extra="none"),
    "dot-field": dict(ko="도트 필드", texture="dots(18px, .08)", bg_extra="none"),
    "duotone-photo": dict(ko="듀오톤 사진", texture="duotone", bg_extra="none"),
}

MOTION = {
    "minimal": dict(ko="거의 없음", dur_fast="120ms", dur_base="180ms", dur_scene="320ms",
                    ease="cubic-bezier(.4,0,.2,1)", stagger="40ms",
                    note="인쇄·문서형. 페이드만, 큰 이동 금지"),
    "composed": dict(ko="정돈된 등장", dur_fast="160ms", dur_base="280ms", dur_scene="560ms",
                     ease="cubic-bezier(.22,1,.36,1)", stagger="70ms",
                     note="섹션 단위 스태거드 리빌 1회"),
    "bold": dict(ko="강한 임팩트", dur_fast="110ms", dur_base="220ms", dur_scene="760ms",
                 ease="cubic-bezier(.16,1,.3,1)", stagger="90ms",
                 note="한 화면 한 번 크게. 연속 마이크로 인터랙션 금지"),
    "playful": dict(ko="발랄한 바운스", dur_fast="140ms", dur_base="300ms", dur_scene="640ms",
                    ease="cubic-bezier(.34,1.56,.64,1)", stagger="80ms",
                    note="작은 오버슈트 허용, 3회 이상 반복 금지"),
    "slow-fade": dict(ko="느린 페이드", dur_fast="240ms", dur_base="420ms", dur_scene="900ms",
                      ease="cubic-bezier(.33,0,.15,1)", stagger="120ms",
                      note="갤러리형. 이동보다 불투명도"),
}

# ── 테마 12종 ──────────────────────────────────────────────────────────────────
THEMES = [
    dict(id="editorial-serif", ko="편집 세리프 (신문·저널)", type="serif-editorial", density="dense",
         shape="rule-only", texture="paper", motion="minimal", dark=False, image="inline-figure + 듀오톤",
         families=["oxblood-archive", "deep-ink", "sand-charcoal"],
         moods=["문학적", "편집", "아카이브", "차분한", "무게감", "editorial"],
         subjects=["논문", "원고", "기록", "증례", "학회", "책", "교재", "출판", "히스토리", "다큐", "에세이"],
         media=["book", "report", "pdf", "newsletter"], avoid=["card", "sns"],
         note="다단·괘선·캡션. 표와 각주가 리듬을 만든다"),
    dict(id="clinical-precise", ko="임상 정밀 (검진·진료)", type="sans-technical", density="dense",
         shape="hairline", texture="flat", motion="minimal", dark=False, image="none / 도식",
         families=["clinical-cool", "slate-mint"],
         moods=["정확한", "청결한", "차분한", "단정한", "clinical"],
         subjects=["검진", "임상", "진료", "내시경", "초음파", "환자 안내", "복약", "가이드라인", "통계"],
         media=["deck", "report", "pdf", "study"], avoid=[],
         note="수치·표·플로우가 주인공. 장식은 괘선뿐"),
    dict(id="swiss-grid", ko="스위스 그리드 (덱·발표)", type="sans-swiss", density="regular",
         shape="hairline", texture="flat", motion="composed", dark=False, image="한 장 큰 도판",
         families=["deep-ink", "cobalt-paper", "clinical-cool"],
         moods=["현대적", "명료한", "단호한", "modern", "grid"],
         subjects=["제안서", "IR", "전략", "제품", "발표", "브리핑", "기업"],
         media=["deck", "site", "report"], avoid=["card"],
         note="좌정렬 12컬럼 + 큰 숫자. 슬라이드당 주장 1개"),
    dict(id="warm-journal", ko="생활 기록 (일상·건강 습관)", type="warm-humanist", density="airy",
         shape="soft", texture="paper", motion="composed", dark=False, image="일러스트 우선",
         families=["warm-clay", "forest-field", "plum-rose"],
         moods=["따뜻한", "정겨운", "편안한", "생활", "돌봄", "warm"],
         subjects=["생활습관", "요리", "레시피", "가족", "습관", "산책", "수면", "일지", "동네"],
         media=["card", "study", "book", "newsletter"], avoid=[],
         note="세리프 제목 + 편한 본문. 손그림 도형, 낮은 밀도"),
    dict(id="brutalist-poster", ko="포스터 임팩트 (SNS·홍보)", type="poster-heavy", density="compressed",
         shape="hard", texture="grain", motion="bold", dark=False, image="도형·타이포만",
         families=["graphite-lime", "cobalt-paper", "oxblood-archive"],
         moods=["강한", "충격적", "직설적", "bold", "poster"],
         subjects=["홍보", "이벤트", "모집", "캠페인", "안내문", "주의", "금연", "절주"],
         media=["card", "sns", "deck"], avoid=["book", "report"],
         note="한 화면 한 문장, 초굵은 제목, 각진 경계"),
    dict(id="terminal-mono", ko="터미널 모노 (기술·데이터)", type="mono-terminal", density="compressed",
         shape="hard", texture="scanlines", motion="minimal", dark=True, image="차트·표",
         families=["graphite-lime", "cobalt-paper", "deep-ink"],
         moods=["기술적", "실험적", "날카로운", "데이터", "terminal"],
         subjects=["코드", "AI", "모델", "벤치마크", "API", "서버", "엔지니어링", "투자", "지표"],
         media=["deck", "study", "newsletter", "report"], avoid=["book"],
         note="어두운 배경 + 형광 1색. 모노 라벨, 표가 화면을 채운다"),
    dict(id="gallery-airy", ko="갤러리 여백 (사진·브랜드)", type="sans-airy", density="airy",
         shape="hairline", texture="flat", motion="slow-fade", dark=False, image="풀블리드 1장",
         families=["sand-charcoal", "deep-ink", "clinical-cool"],
         moods=["조용한", "고급스러운", "여백", "감성", "gallery"],
         subjects=["포트폴리오", "브랜드", "제품 소개", "전시", "여행", "사진", "기념"],
         media=["site", "book", "deck"], avoid=["card"],
         note="화면당 메시지 1개. 이동보다 불투명도"),
    dict(id="document-plain", ko="실무 문서 (보고·워크북)", type="sans-plain", density="dense",
         shape="rule-only", texture="flat", motion="minimal", dark=False, image="표·도해",
         families=["deep-ink", "sand-charcoal", "clinical-cool"],
         moods=["실무적", "정돈된", "학습", "공문", "plain"],
         subjects=["워크북", "학습", "매뉴얼", "체크리스트", "보고서", "정부", "예산", "시험", "요약"],
         media=["report", "pdf", "workbook", "study", "cuecard"], avoid=["card", "sns"],
         note="장식 0. 번호·표·체크박스. 흑백 인쇄 안전"),
    dict(id="playful-geometric", ko="기하 친근 (환자 교육·안내)", type="rounded-geometric", density="airy",
         shape="soft", texture="dot-field", motion="playful", dark=False, image="도형 일러스트",
         families=["slate-mint", "cobalt-paper", "warm-clay"],
         moods=["친근한", "쉬운", "밝은", "발랄한", "friendly"],
         subjects=["환자 교육", "예방", "접종", "어린이", "생활 안내", "습관 교정", "설문"],
         media=["card", "site", "deck", "study"], avoid=["report"],
         note="둥근 도형·아이콘. 문장 짧게, 한 카드 한 메시지"),
    dict(id="literary-classic", ko="고전 문학 (에세이·칼럼)", type="serif-classic", density="regular",
         shape="rule-only", texture="paper", motion="minimal", dark=False, image="드물게, 작게",
         families=["oxblood-archive", "plum-rose", "deep-ink"],
         moods=["고전적", "문학적", "차분한", "essay", "classic"],
         subjects=["칼럼", "에세이", "서평", "인문", "역사", "고전", "편지", "추천사"],
         media=["newsletter", "book", "study"], avoid=["card"],
         note="이탤릭 캡션·골드 괘선. 본문이 주인공"),
    dict(id="technical-blueprint", ko="설계 도면 (공학·기술서)", type="sans-technical", density="compressed",
         shape="hard", texture="blueprint-grid", motion="minimal", dark=False, image="도식·치수 주석",
         families=["cobalt-paper", "clinical-cool", "graphite-lime"],
         moods=["기술적", "치밀한", "설계", "blueprint"],
         subjects=["설계", "아키텍처", "회로", "공정", "장비", "매뉴얼", "기술서", "측정", "프로토콜"],
         media=["report", "book", "study", "deck"], avoid=["card", "sns"],
         note="배경 그리드·점선·주석 번호. 도식이 본문을 대신한다"),
    dict(id="photo-documentary", ko="사진 기록 (풀블리드)", type="sans-airy", density="airy",
         shape="hard", texture="duotone-photo", motion="slow-fade", dark=False, image="풀블리드 사진 + 작은 캡션",
         families=["warm-clay", "forest-field", "oxblood-archive"],
         moods=["기록", "현장", "사진", "리포트", "documentary"],
         subjects=["현장", "여행", "음식", "사진", "기록", "탐방", "리뷰"],
         media=["card", "site", "book"], avoid=["report"],
         note="텍스트는 사진 위 최소. 색은 사진에서 뽑는다(fetch-image.sh)"),
]
THEME_BY_ID = {t["id"]: t for t in THEMES}

MEDIA_ALIAS = {"web": "site", "landing": "site", "sns": "card", "screen": "site", "pdf": "pdf"}


# ── 유틸 ────────────────────────────────────────────────────────────────────────


def _seed_int(seed: str) -> int:
    import hashlib
    return int(hashlib.sha256((seed or "x").encode()).hexdigest()[:12], 16)


def history(limit: int = 12) -> list[dict]:
    if not HISTORY.exists():
        return []
    rows = []
    try:
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return []
    return rows[-limit:]


def rank(subject: str, medium: str, mood: str, seed: str, exclude: set[str],
         exclude_recent: bool, force: str) -> list[dict]:
    text = f"{subject} {mood}".lower()
    hist = history()
    recent_ids = [r.get("theme", "") for r in hist]
    recent_fp = [r.get("fingerprint", "") for r in hist]
    med = MEDIA_ALIAS.get(medium, medium)
    seed_i = _seed_int(seed or subject or med)
    out = []
    for i, th in enumerate(THEMES):
        hits = [k for k in th["moods"] + th["subjects"] if k.lower() in text]
        score = 3.0 * len(hits)
        if med in th["media"]:
            score += 2.5
        if med in th["avoid"]:
            score -= 100.0
        if th["id"] in exclude:
            score -= 100.0
        if exclude_recent and th["id"] in recent_ids:
            score -= 4.0 * recent_ids.count(th["id"])
        if force:
            score = 999.0 if th["id"] == force else -999.0
        fp = f"{th['id']}|{th['type']}|{th['density']}|{th['shape']}|{th['texture']}|{'dark' if th['dark'] else 'light'}"
        out.append({"theme": th, "score": score, "hits": hits, "fingerprint": fp,
                    "repeat_fp": th["id"] in recent_ids or fp in recent_fp})
    out.sort(key=lambda r: (-r["score"], (seed_i + THEMES.index(r["theme"])) % 991))
    return out


def pick_family(th: dict, subject: str, medium: str, mood: str, seed: str, exclude_fam: set[str]) -> dict:
    ranked = PA.rank(subject, medium, mood, seed, exclude_fam, False)
    pref = [r for r in ranked if r["family"]["name"] in th["families"]]
    return (pref or ranked)[0]


def dark_variant(tokens: dict, fam: dict) -> dict:
    """다크 테마: 표면 사다리를 어둡게 뒤집고 텍스트를 흰 쪽으로 맞춘다(대비는 계산으로 보장).

    어두운 배경에서는 악센트를 **밝은 쪽으로** 다시 맞추고(4.5:1), 악센트 위 글자는 흰색이 아니라
    **어두운 표면색**을 쓴다(밝은 악센트에 흰 글자는 대비가 안 나온다 — 실측 1.86:1 오류).
    """
    base = tokens["--color-surface-inverse"]
    s1 = PA.mix(base, "#FFFFFF", 0.06)
    s2 = PA.mix(base, "#FFFFFF", 0.12)
    out = dict(tokens)
    out["--color-surface-0"] = base
    out["--color-surface-1"] = s1
    out["--color-surface-2"] = s2
    out["--color-text-1"] = PA.fit_contrast("#F5F3F0", s2, 10.0, "white")
    out["--color-text-2"] = PA.fit_contrast(PA.mix(out["--color-text-1"], base, 0.28), s2, 5.0, "white")
    out["--color-text-3"] = PA.fit_contrast(PA.mix(out["--color-text-1"], base, 0.18), s2, 4.5, "white")
    out["--color-border"] = PA.rgba("#FFFFFF", 0.16)
    out["--color-border-strong"] = PA.rgba("#FFFFFF", 0.34)
    out["--color-surface-overlay"] = PA.rgba(base, 0.78)
    # 악센트는 밝게 다시 맞추고, 악센트 위 글자는 어두운 표면색으로
    accent = PA.fit_contrast(tokens["--color-accent"], s2, 4.5, "white")
    out["--color-accent"] = accent
    out["--color-accent-quiet"] = PA.mix(accent, base, 0.78)
    out["--color-accent-strong"] = PA.fit_contrast(accent, s2, 7.0, "white")
    out["--color-text-on-accent"] = PA.fit_contrast(base, accent, 4.5, "black")
    # 반대(inverted) 블록 = 밝은 표면
    out["--color-surface-inverse"] = fam["surfaces"][0]
    out["--color-text-on-inverse"] = PA.fit_contrast(fam["ink"], fam["surfaces"][0], 4.5)
    return out


def dark_checks(tokens: dict) -> list[dict]:
    checks = []
    s0, s2 = tokens["--color-surface-0"], tokens["--color-surface-2"]
    for key, target in (("--color-text-1", 7.0), ("--color-text-2", 4.5), ("--color-text-3", 4.5),
                        ("--color-accent", 4.5)):
        r = PA.contrast(tokens[key], s2)
        checks.append({"label": f"{key} on surface-2 (dark)", "fg": tokens[key], "bg": s2,
                       "ratio": round(r, 2), "target": target, "ok": r + 1e-9 >= target})
    r = PA.contrast(tokens["--color-text-1"], s0)
    checks.append({"label": "text-1 on surface-0 (dark)", "fg": tokens["--color-text-1"], "bg": s0,
                   "ratio": round(r, 2), "target": 7.0, "ok": r + 1e-9 >= 7.0})
    r = PA.contrast(tokens["--color-text-on-accent"], tokens["--color-accent"])
    checks.append({"label": "text-on-accent on accent (dark)", "fg": tokens["--color-text-on-accent"],
                   "bg": tokens["--color-accent"], "ratio": round(r, 2), "target": 4.5,
                   "ok": r + 1e-9 >= 4.5})
    r = PA.contrast(tokens["--color-text-on-inverse"], tokens["--color-surface-inverse"])
    checks.append({"label": "text-on-inverse on inverted block", "fg": tokens["--color-text-on-inverse"],
                   "bg": tokens["--color-surface-inverse"], "ratio": round(r, 2), "target": 4.5,
                   "ok": r + 1e-9 >= 4.5})
    return checks



def build(theme: dict, fam_entry: dict, subject: str, medium: str) -> dict:
    fam, accent = fam_entry["family"], fam_entry["accent"]
    color, checks = PA.build_tokens(fam, accent, medium)
    if theme["dark"]:
        color = dark_variant(color, fam)
        checks = dark_checks(color)
    ty, de, sh, tx, mo = TYPE[theme["type"]], DENSITY[theme["density"]], SHAPE[theme["shape"]], \
        TEXTURE[theme["texture"]], MOTION[theme["motion"]]
    tokens = {**color,
              "--font-display": ty["display"], "--font-body": ty["body"], "--font-mono": ty["mono"],
              "--text-display": ty["h"], "--text-h1": ty["h1"], "--text-h2": ty["h2"], "--text-h3": ty["h3"],
              "--text-body": ty["body_size"], "--text-small": ty["small"],
              "--leading-body": str(ty["leading_body"]), "--leading-heading": str(ty["leading_heading"]),
              "--tracking-display": ty["tracking_display"], "--tracking-body": ty["tracking_body"],
              "--space-base": de["space_base"], "--space-4": de["space_4"],
              "--space-12": de["space_12"], "--space-24": de["space_24"],
              "--section-y": de["section_y"], "--section-y-lg": de["section_y_lg"],
              "--container-max": de["container_max"], "--pad-x": de["pad_x"], "--maxw": de["container_max"],
              "--radius-sm": sh["radius_sm"], "--radius-md": sh["radius_md"], "--radius-pill": sh["radius_pill"],
              "--shadow-lift": sh["shadow_lift"], "--shadow-overlay": sh["shadow_overlay"],
              "--surface-texture": tx["texture"], "--surface-bg-extra": tx["bg_extra"],
              "--duration-fast": mo["dur_fast"], "--duration-base": mo["dur_base"],
              "--duration-scene": mo["dur_scene"], "--ease-standard": mo["ease"], "--stagger-step": mo["stagger"]}
    checks = checks + [
        {"label": "제목/본문 타이포 대비 (단조 방지)", "fg": "-", "bg": "-", "ratio": 0.0,
         "target": 0.0,
         "ok": ty["display"].split(",")[0] != ty["body"].split(",")[0] or bool(ty.get("single_family")),
         "note": (f"{ty['display'].split(',')[0]} / {ty['body'].split(',')[0]}"
                  + (f" — 한 패밀리, {ty['single_family']}" if ty.get("single_family") else ""))},
        {"label": f"제목 크기 {ty['h']} · 밀도 {de['ko']} ({de['section_y']})", "fg": "-", "bg": "-",
         "ratio": 0.0, "target": 0.0, "ok": True, "note": f"type={theme['type']} density={theme['density']}"},
    ]
    return {"theme": theme, "family": fam, "accent": accent, "tokens": tokens, "checks": checks,
            "type": ty, "density": de, "shape": sh, "texture": tx, "motion": mo}


def tokens_css(built: dict, subject: str, medium: str) -> str:
    th, ty, de, mo = built["theme"], built["type"], built["density"], built["motion"]
    lines = [
        "/* design-craft — theme-advisor 로 생성한 토큰 (테마 전체).",
        f" * theme: {th['id']} ({th['ko']}) · fingerprint: {th['id']}|{th['type']}|{th['density']}|"
        f"{th['shape']}|{th['texture']}|{'dark' if th['dark'] else 'light'}",
        f" * color family: {built['family']['name']} ({built['family']['ko']}) · accent {built['accent']}"
        f" · 매체 {medium} · 대상 {subject or '(미지정)'}",
        f" * 타이포: {ty['ko']} · 밀도: {de['ko']} · 질감: {built['texture']['ko']} · 모션: {mo['ko']}",
        f" * 이미지: {th['image']}",
        f" * 규칙: {th['note']}",
        f" * 모션 주의: {mo['note']}",
    ]
    if ty.get("font_link"):
        lines.append(f" * 웹폰트(HTML head 에 넣는다): {ty['font_link']}")
    lines.append(" */")
    lines.append(":root {")
    for k, v in built["tokens"].items():
        lines.append(f"  {k}: {v};")
    lines += [
        "}",
        "",
        "/* 질감은 배경 레이어로 구현한다(토큰 값만 보고 손으로 hex 를 만들지 않는다):",
        "   --surface-texture: grain|scanlines|grid|dots|duotone|none  ·  --surface-bg-extra: 배경 레이어 */",
        "/* 인쇄(PDF·책)면 질감·그림자를 끄고 괘선·굵기로 위계를 만든다. */",
    ]
    return "\n".join(lines) + "\n"


# ── report ─────────────────────────────────────────────────────────────────────


def report(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    rc = PA.report_file(path)
    print("[theme report]")
    fp = re.search(r"fingerprint: ([^ *]+)", text)
    th_id = fp.group(1).split("|")[0] if fp else ""
    known = THEME_BY_ID.get(th_id)
    print(f"  {'PASS' if known else 'note'}  테마 지문: {fp.group(1) if fp else '없음 (theme-advisor 로 만들지 않음)'}")
    if known:
        print(f"        테마 {known['id']} ({known['ko']}) — {known['note']}")
    fonts = dict(re.findall(r"--font-(display|body):\s*([^;]+);", text))
    if fonts.get("display") and fonts.get("body"):
        same = fonts["display"].split(",")[0].strip() == fonts["body"].split(",")[0].strip()
        single = bool(known and TYPE[known["type"]].get("single_family"))
        ok = (not same) or single
        tag = "PASS" if ok else ("WARN" if known else "note")
        detail = f"한 패밀리, {TYPE[known['type']]['single_family']}" if single else ""
        print(f"  {tag}  타이포 단조: display {fonts['display'].split(',')[0]} / "
              f"body {fonts['body'].split(',')[0]}{' — ' + detail if detail else ''}"
              + ("" if known else " (테마 지문이 없어 단조 여부는 판단하지 않음)"))
    probes = (("--section-y", "섹션 리듬", r"--section-y|--space-12|--space-24"),
              ("--pad-x", "좌우 여백", r"--[a-z-]*pad-x[a-z-]*"),
              ("--surface-texture", "질감", r"--surface-texture"))
    for label_key, label, pattern in probes:
        m = re.search(rf"({pattern}):\s*([^;]+);", text)
        val = m.group(2).strip() if m else ""
        if m:
            note = "  (질감 없음 = 인쇄·문서형이면 정상)" if label_key == "--surface-texture" else ""
            print(f"  PASS  {label}: {m.group(1)} = {val}{note}")
        else:
            tag = "WARN" if known else "note"
            print(f"  {tag}  {label}: 없음"
                  + ("" if known else " (테마 지문이 없어 판단하지 않음 — 큐카드·기존 파일이면 정상)"))
    return rc


# ── main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="산출물에 맞는 테마(색+타이포+밀도+질감+모션)를 고른다")
    ap.add_argument("--subject", default="")
    ap.add_argument("--medium", default="screen",
                    choices=["screen", "web", "site", "landing", "card", "sns", "deck", "pdf", "report", "book",
                             "workbook", "study", "cuecard", "newsletter", "illus", "motion"])
    ap.add_argument("--mood", default="")
    ap.add_argument("--seed", default="")
    ap.add_argument("--theme", choices=sorted(THEME_BY_ID), help="테마를 직접 지정")
    ap.add_argument("--exclude-theme", action="append", default=[], help="제외할 테마 id")
    ap.add_argument("--exclude-family", action="append", default=[], help="제외할 색 계열")
    ap.add_argument("--exclude-recent", action="store_true", help="최근 쓴 테마를 감점")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--write", metavar="PATH")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--history", nargs="?", type=int, const=8, metavar="N")
    ap.add_argument("--report", metavar="FILE")
    args = ap.parse_args(argv)

    if args.list:
        for th in THEMES:
            print(f"{th['id']:20s} {th['ko']:26s} type={th['type']:18s} density={th['density']:10s} "
                  f"질감={th['texture']:14s} 모션={th['motion']:10s} {'dark' if th['dark'] else 'light'} "
                  f"매체={','.join(th['media'][:3])}")
        return 0

    if args.report is not None:
        p = Path(args.report)
        if not p.exists():
            print(f"파일이 없다: {p}", file=sys.stderr)
            return 2
        return report(p)

    if args.history is not None:
        rows = history(args.history)
        if not rows:
            print(f"히스토리 없음: {HISTORY}")
            return 0
        for r in rows:
            print(f"{r.get('ts','')}  {r.get('theme',''):20s} {r.get('family',''):16s} "
                  f"{r.get('accent','')}  {r.get('fingerprint','')}")
            print(f"    {r.get('subject','')[:70]} · {r.get('medium','')}")
        return 0

    subject = args.subject.strip()
    if not subject and not args.mood and not args.theme:
        print("--subject 또는 --mood 또는 --theme 이 필요하다.", file=sys.stderr)
        return 2

    ranked = rank(subject, args.medium, args.mood, args.seed or subject,
                  set(args.exclude_theme), args.exclude_recent, args.theme or "")
    picks = []
    fam_used = set(args.exclude_family)
    for entry in ranked[: max(1, args.top)]:
        fam_entry = pick_family(entry["theme"], subject, args.medium, args.mood, args.seed or subject, fam_used)
        fam_used.add(fam_entry["family"]["name"])
        picks.append({**entry, "fam_entry": fam_entry, "built": build(entry["theme"], fam_entry, subject, args.medium)})
    top = picks[0]
    failed = [c for c in top["built"]["checks"] if not c["ok"]]

    if args.json:
        print(json.dumps({
            "subject": subject, "medium": args.medium, "mood": args.mood,
            "recent": [{"theme": r.get("theme"), "fingerprint": r.get("fingerprint")} for r in history(6)],
            "candidates": [{
                "theme": p["theme"]["id"], "ko": p["theme"]["ko"], "score": round(p["score"], 2),
                "fingerprint": p["fingerprint"], "hits": p["hits"], "repeat": p["repeat_fp"],
                "image": p["theme"]["image"], "note": p["theme"]["note"],
                "family": p["fam_entry"]["family"]["name"], "accent": p["fam_entry"]["accent"],
                "tokens": p["built"]["tokens"], "checks": p["built"]["checks"],
            } for p in picks],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"[theme] {subject or '(주제 없음)'} · 매체 {args.medium}" + (f" · 무드 {args.mood}" if args.mood else ""))
        hist = history(6)
        if hist:
            print("  최근: " + " · ".join(f"{r.get('theme')}({r.get('family')})" for r in hist))
        for n, p in enumerate(picks):
            th, ty, de = p["theme"], p["built"]["type"], p["built"]["density"]
            print(f"\n  [{n + 1}] {th['id']} ({th['ko']}) score={p['score']:.1f}"
                  f"{'  ← 1순위' if n == 0 else ''}{'  ⚠ 최근에 씀(같은 느낌)' if p['repeat_fp'] else ''}")
            print(f"      타이포 {ty['ko']} · 밀도 {de['ko']} · 질감 {p['built']['texture']['ko']}"
                  f" · 모션 {p['built']['motion']['ko']} · {'dark' if th['dark'] else 'light'}")
            print(f"      색 {p['fam_entry']['family']['name']} · 악센트 {p['fam_entry']['accent']}"
                  f" · 이미지 {th['image']}")
            if p["hits"]:
                print(f"      맞은 키워드: {', '.join(p['hits'][:8])}")
        print("\n  검사 (1순위):")
        for c in top["built"]["checks"]:
            tag = "PASS" if c["ok"] else "FAIL"
            extra = f" — {c['note']}" if c.get("note") else ""
            ratio = f" {c['ratio']}:1" if c["ratio"] else ""
            print(f"    {tag}  {c['label']}{ratio}{extra}")
        if [p for p in picks if p["repeat_fp"]]:
            print("\n  ⚠ 후보 중 최근 것과 같은 느낌(fingerprint)이 있다 — 다르게 하려면 "
                  "--exclude-theme <id> 또는 --exclude-recent 로 다시 고른다.")

    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(tokens_css(top["built"], subject, args.medium), encoding="utf-8")
        print(f"\n  wrote {out}")
        if top["built"]["type"].get("font_link"):
            print(f"  웹폰트 <link> 필요: {top['built']['type']['font_link']}")

    if args.record or args.write:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "theme": top["theme"]["id"], "fingerprint": top["fingerprint"],
                "family": top["fam_entry"]["family"]["name"], "accent": top["fam_entry"]["accent"],
                "subject": subject, "medium": args.medium, "mood": args.mood,
            }, ensure_ascii=False) + "\n")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
