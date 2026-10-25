# 테마 — 산출물 종류마다 다른 느낌 (색만으로는 부족하다)

**문제**: 색을 고쳐도 카드뉴스·책·발표자료가 여전히 닮는다. 이유는 색이 아니라 **나머지가 고정**이기
때문이다 — 같은 산세리프, 같은 라운드, 같은 여백 리듬, 같은 질감 없음, 같은 등장 모션. 폰트와 밀도와
질감이 매체와 무관하게 하나면, 팔레트만 바뀌어도 "같은 디자이너가 색만 바꿔서 낸 것"이 된다.

**해법**: 한 산출물의 **테마 전체**를 고른다 = ⓐ 색 계열 ⓑ 타이포(폰트 페어·스케일·자간·행간)
ⓒ 밀도(여백·섹션 리듬·컨테이너) ⓓ 형태(반경·그림자·경계) ⓔ 질감(종이·그레인·그리드·스캔라인·도트)
ⓕ 명암(light/dark) ⓖ 이미지 처리 ⓗ 모션 성격. 도구는 `scripts/theme-advisor.py`
(색은 `palette-advisor.py` 에 위임한다 — 색 단독이 필요하면 그쪽만 쓴다).

```bash
T=~/.config/opencode/skills/design-craft/scripts/theme-advisor.py
python3 $T --subject "미국 주식 투자레터" --medium newsletter --mood "분석적, 데이터"   # 테마 후보 3
python3 $T --theme terminal-mono --medium study --subject "딥러닝 벤치마크" --write build/tokens.css
python3 $T --history 8        # 최근 테마·fingerprint  → 반복 감지
python3 $T --report build/tokens.css   # 색 대비 + 테마 지문 + 타이포 단조 + 밀도·질감 유무
```

## 1. 매체가 1차 필터다

같은 "차분한" 주제라도 매체가 다르면 다른 테마가 나온다(같은 입력으로 실측):

| 매체 | 실측 1순위 | 왜 |
|---|---|---|
| 카드뉴스(환자 안내) | `playful-geometric` | 한 장 한 메시지, 둥근 도형, 발랄한 모션 |
| 투자레터 | `terminal-mono` (dark) | 표·수치가 주인공, 압축 밀도, 모노 라벨 |
| 요리·생활 카드 | `warm-journal` | 세리프 제목 + 편한 본문, 종이 질감, 여유 |
| 학습자료(기술) | `terminal-mono`/`technical-blueprint` | 도식·수치, 압축 밀도, 배경 그리드 |
| 검진 안내문(PDF) | `clinical-precise` | 수치·표 중심, 장식 0, 거의 없는 모션 |
| 발표 제안서 | `swiss-grid` | 좌정렬 12컬럼, 슬라이드당 주장 1개 |
| 워크북 | `document-plain` | 장식 0, 번호·표, 흑백 인쇄 안전 |

## 2. 테마 12종 (`--list` 와 같은 표)

- **`editorial-serif` 편집 세리프** — 신문·저널·논문·원고·증례. 세리프 디스플레이 + 세리프 본문,
  촘촘, 괘선만, 종이 질감, 모션 거의 없음. 매체: book·report·pdf·newsletter.
- **`clinical-precise` 임상 정밀** — 검진·진료·통계·가이드라인. 기술 산세리프, 촘촘, 헤어라인, 평면,
  모션 없음. 매체: deck·report·pdf·study.
- **`swiss-grid` 스위스 그리드** — 제안서·IR·전략·제품. 산세리프 단일 패밀리(굵기·자간으로 대비),
  보통 밀도, 헤어라인, 평면, 정돈된 등장. 매체: deck·site·report.
- **`warm-journal` 생활 기록** — 요리·생활습관·가족·돌봄. 세리프 제목 + 휴머니스트 본문, 여유, 부드러운
  면, 종이 질감, 정돈된 등장. 매체: card·study·book·newsletter.
- **`brutalist-poster` 포스터 임팩트** — 홍보·모집·캠페인·주의 환기. 초굵은 제목, 압축, 각진 경계,
  그레인, 강한 모션. 매체: card·sns·deck. (book·report 에는 쓰지 않는다)
- **`terminal-mono` 터미널 모노(dark)** — 코드·AI·벤치마크·지표·투자. 모노 디스플레이, 압축, 각진 경계,
  스캔라인, 모션 없음. 어두운 배경 + 밝은 악센트. 매체: deck·study·newsletter·report.
- **`gallery-airy` 갤러리 여백** — 포트폴리오·브랜드·전시·사진. 여백 산세리프, 매우 여유, 헤어라인,
  평면, 느린 페이드. 매체: site·book·deck.
- **`document-plain` 실무 문서** — 워크북·매뉴얼·체크리스트·보고·정부. 실무 산세리프(크기·번호로 대비),
  촘촘, 괘선만, 평면, 모션 없음. 매체: report·pdf·workbook·study·cuecard.
- **`playful-geometric` 기하 친근** — 환자 교육·예방·접종·어린이·습관 교정. 라운드 산세리프, 여유,
  부드러운 면, 도트 필드, 발랄한 바운스. 매체: card·site·deck·study.
- **`literary-classic` 고전 문학** — 칼럼·에세이·서평·인문. 고전 세리프(굵기·이탤릭 캡션으로 대비),
  보통, 괘선만, 종이, 모션 없음. 매체: newsletter·book·study.
- **`technical-blueprint` 설계 도면** — 설계·아키텍처·공정·장비·프로토콜. 기술 산세리프 + 모노 라벨,
  압축, 각진 경계, 설계 그리드, 모션 없음. 매체: report·book·study·deck.
- **`photo-documentary` 사진 기록** — 현장·여행·음식·탐방. 여백 산세리프, 여유, 각진 경계, 듀오톤 사진,
  느린 페이드. 매체: card·site·book. 색은 사진에서 뽑는다(`card-craft/scripts/fetch-image.sh`).

## 3. 하부 스킬과의 연결 (여기서 갈라진다)

테마는 부모가 고르고, 표면별 구현은 하부 스킬이 한다. 겹치면 하부 스킬이 이긴다.

- **deck-craft** — 청중 유형이 테마 후보를 좁힌다:
  `academic` → `editorial-serif`·`clinical-precise` / `corporate` → `swiss-grid` /
  `government` → `document-plain` / `education` → `playful-geometric`·`warm-journal` /
  `internal` → `document-plain`·`swiss-grid`. 슬라이드 유형 13종·발표장 조명 규칙은 그대로.
- **card-craft** — 레이아웃 10종은 테마가 아니라 **구성**이다. 테마는 톤(폰트·밀도·질감·모션)을 정하고,
  같은 테마 안에서 레이아웃을 섞는다(예: `warm-journal` + `list`/`quote`/`photo-split`).
- **book-craft** — 테마는 제목·괘선·질감을, `typesetting.md` 는 판형·여백·고아·각주를 정한다.
  인쇄면 질감·그림자를 끄고 괘선·굵기로 위계를 만든다.
- **site-craft** — 테마의 밀도·폰트가 히어로/섹션 리듬을 정하고, SEO·메타·법정 푸터는 그대로.
- **study-craft** — 다크가 기본이면 테마도 dark 계열(`terminal-mono`)이 맞는다.
- **illus-craft** — 그림 톤은 테마의 명암·채도에서 파생한다(`--ink`·`--muted` 를 테마 토큰에서 뽑는다).
- **motion-craft** — 테마의 모션 프리셋(minimal/composed/bold/playful/slow-fade)이 duration·easing·
  stagger 를 정한다. 모션 레시피 선택은 그 위에서 한다.
- **ml-dl-workbook** — 입문 워크북(A4 PDF). 수식·도식 중심 `technical-blueprint`, 코드·실습 중심
  `terminal-mono`(인쇄는 `@media print` 로 밝게), 비유·입문 `warm-journal`, 연습·정답 비중 큼
  `document-plain`. 토큰 파일은 `assets/workbook.tokens.css` 하나이고 색·폰트·크기 블록만 교체한다.
- **script-to-cuecards** — 인쇄 큐카드. 기본 `document-plain`, 낭독 리허설이면 `editorial-serif`
  (`brutalist-poster` 금지). **색 위주로** 바꾸고 재단 기하(`--pad-y`·`--card-h`·`--cut`)는 고정한다 —
  A4 한 장에 148.3 mm 카드 두 장이 들어가는 실측 기하가 검증 대상이다. **폰트는 설치된 것만**
  (미설치 스택은 블록 탈락을 만든다 — 실측 1블록).
- **인쇄(PDF·책·큐카드·워크북) 공통**: 질감·그림자를 끄고, 폰트는 그 인쇄 환경에 있는 것(또는 HTML 에
  웹폰트 `<link>` 를 넣는 경우에만 웹폰트)으로 확정한다. 테마 `--write` 가 웹폰트 링크를 출력하면
  HTML 산출물(워크북·사이트·덱)에는 넣고, **큐카드처럼 생성기가 head 를 통제하는 PDF 에는 넣지 않는다**.

## 4. 반복 감지 — fingerprint

테마+타이포+밀도+형태+질감+명암을 한 줄로 묶은 **fingerprint** 를 히스토리
(`~/.cache/design-craft/theme-history.jsonl`)에 남기고, 다음 선택에서 `⚠ 최근에 씀(같은 느낌)` 을 붙인다.

- 같은 주제·같은 매체를 다시 만들 때 **같은 테마는 맞다**(시리즈 일관성). 그때는 그대로 쓰고
  `--seed` 로 악센트만 흔든다.
- **다른 매체인데 같은 fingerprint** 면 실패다 → `--exclude-theme <id>` 또는 `--exclude-recent`.
- 예외: 브랜드/시리즈 팔레트 고정(invest-newsletter 카드). 그때도 타이포·밀도는 매체에 맞춘다.

## 5. 검증 (넘기기 전)

```bash
python3 $T --report build/tokens.css     # 색 대비 + 테마 지문 + 타이포 단조 + 밀도·질감 유무
python3 $S/design-lint.py <dir> --tokens build/tokens.css    # AI 티·하드코딩 (0 HIGH)
python3 $S/page-check.sh <html> --width <매체폭>              # 기하·대비·어절 (0 HIGH/0 MED)
```

- `--report` 가 `테마 지문: 없음` 이면 **theme-advisor 를 거치지 않은 것**이다(템플릿 기본값 위험).
- `타이포 단조: WARN` 은 제목·본문이 같은 폰트이면서 의도적 장치(굵기·자간·크기)가 없는 경우다.
- 검증 후 제시 메시지에 **한 줄**: `테마: warm-journal (생활 기록) · 색 warm-clay · 악센트 #8A5A2B · 대비 PASS`.
