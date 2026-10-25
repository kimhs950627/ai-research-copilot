# Design taxonomy — 정확한 용어로 지시하기

디자인 결과의 품질은 프롬프트 기교가 아니라 **정확한 전문용어**에서 나온다. "부드럽게 나타나게
해줘" 대신 `staggered reveal with 60ms delay per item` 이라고 써야 그 결과가 나온다. 이 문서는
프롬프트에 그대로 붙여 쓸 수 있는 용어 사전이다.

쓰는 법: 어떤 효과를 원하는지 먼저 한국어로 적고, 아래 표에서 **영문 정식 명칭**을 찾아 프롬프트에
그대로 넣는다. 필요하면 파라미터(duration, easing, distance)까지 명시한다.

## 1. 레이아웃 · 조판

| 원하는 것 | 용어 | 프롬프트 예 |
|---|---|---|
| 화면 전체를 덮는 첫 화면 | Full-bleed hero | `full-bleed hero with a 92vh media panel` |
| 좌우 여백에 줄이 그어진 격자 | Line grid / trellis | `subtle 1px line grid overlay, 12 columns, 8% opacity` |
| 기준선에 맞춘 정렬 | Optical alignment / baseline grid | `align headings to an 8px baseline grid` |
| 화면 폭에 따라 자연스럽게 커지는 글자 | Fluid type (clamp) | `font-size: clamp(2.5rem, 6vw, 5.5rem)` |
| 그리드를 일부러 깨는 요소 | Grid break / bleed | `let the image bleed 2 columns past the grid` |
| 비대칭 2단 | Asymmetric split | `7/5 asymmetric split, text left, media right` |
| 스크롤 중 고정되는 영역 | Sticky / pinned section | `pin the heading while the gallery scrolls` |
| 겹쳐 놓은 레이어 | Overlap / layered composition | `type overlapping the media by 40px` |
| 대각선 흐름 | Diagonal flow | `section divider as a 4deg diagonal` |
| 요소를 화면 끝까지 밀어내는 배치 | Edge-to-edge / marquee row | `edge-to-edge horizontal row, no container padding` |
| 카드가 흘러가는 띠 | Marquee / infinite ticker | `infinite marquee, 40s linear, pauses on hover` |

## 2. 모션 · 인터랙션

| 원하는 것 | 용어 | 프롬프트 예 |
|---|---|---|
| 목록이 순차 등장 | Staggered reveal | `stagger children 60ms, translateY(16px) → 0, 500ms` |
| 카드 클릭 시 이미지가 이어져 확대 | Shared layout animation (shared element transition) | `shared layout animation between card image and detail hero image (Framer Motion layoutId)` |
| 스크롤에 따라 진행되는 애니메이션 | Scroll-driven animation / scroll-linked | `scroll-scrubbed timeline, tied to scroll progress 0→1` |
| 스크롤하면 가로로 이동 | Horizontal scroll on vertical scroll | `translateX pan tied to scrollY, 3 panels, with a synced timeline bar` |
| 특정 위치에 닿았을 때 1회 재생 | Scroll-triggered / viewport enter | `animate once on enter, threshold 0.3` |
| 배경이 천천히 따라 움직임 | Parallax | `parallax at 0.35 speed on the background layer` |
| 페이지 전환 자체를 애니메이션 | View Transition API / cross-fade | `document.startViewTransition on link navigation` |
| 마우스를 따라오는 커서 | Custom cursor / magnetic | `magnetic cursor snapping 8px to interactive elements` |
| 마스크가 걷히며 나타남 | Mask reveal / clip-path wipe | `clip-path inset wipe reveal, 700ms cubic-bezier(.22,1,.36,1)` |
| 글자가 한 글자씩 | Text split / character reveal | `split text reveal, 30ms per character` |
| 자석처럼 붙는 버튼 | Magnetic button | `magnetic button, max offset 6px` |
| 스크롤 위치 진행 바 | Scroll progress indicator | `top progress bar bound to scrollY/scrollHeight` |
| 낮/밤 이미지 블렌딩 | Cross-fade opacity blending | `two stacked images, day opacity 0.75 / night 0.25` |

기본 파라미터 감각: 마이크로 인터랙션 120–200ms, 등장 400–700ms, 페이지 전환 300–500ms.
easing 은 `cubic-bezier(.22,1,.36,1)` (out-expo 계열) 또는 `cubic-bezier(.4,0,.2,1)`.
`prefers-reduced-motion` 분기를 항상 넣는다.

## 3. 컴포넌트 · 패턴

| 용어 | 설명 |
|---|---|
| Bento grid | 크기가 다른 카드가 모자이크처럼 채우는 그리드 |
| Masonry | 높이가 다른 카드가 빈틈없이 쌓이는 배치 |
| Sticky sidebar / TOC | 상세 페이지에서 목차가 따라다니는 패턴 |
| Command palette (⌘K) | 키보드로 여는 검색/명령 오버레이 |
| Segmented control | 붙어 있는 알약형 탭 |
| Disclosure / accordion | 접고 펴는 상세 |
| Toast / inline validation | 피드백 전달 방식 |
| Empty / loading / error state | 상태 3종 세트 — 앱이면 반드시 정의 |
| Skip link | 키보드 사용자용 본문 건너뛰기 |
| Focus-visible ring | 키보드 포커스 표시 |
| Skeleton screen | 로딩 자리표시자 |

## 4. 타이포그래피

| 용어 | 뜻 |
|---|---|
| Display / body pair | 성격 있는 제목 폰트 + 읽기 좋은 본문 폰트 |
| Modular scale | 1.25 / 1.333 비율로 크기 단계를 만드는 방식 |
| Measure (line length) | 한 줄 길이. 본문 45–75자 |
| Leading / tracking | 행간 / 자간. 큰 제목은 자간을 좁힌다(-0.02em) |
| Optical sizing / variable font | 축을 조절하는 가변 폰트 |
| Tabular numerals | 숫자 폭 고정 (표·가격) |
| Font subsetting | 필요한 글자만 잘라 성능 확보 (한글은 필수에 가깝다) |

## 5. 색 · 재질

| 용어 | 뜻 |
|---|---|
| Design token | 색·간격·반경을 이름으로 관리하는 값 |
| Warm black / off-black | 순수 검정 대신 쓰는 웜톤 검정 (`#1A1714`) |
| Dominant + accent | 지배색 하나 + 날카로운 악센트 |
| Gradient mesh / grain | 그라디언트 메시 / 노이즈 그레인으로 깊이 주기 |
| Layered transparency | 반투명 레이어 겹치기 |
| Duotone | 두 색으로 이미지를 통일 |
| Contrast ratio | 대비비. 본문 4.5:1 이상 |
| Contrast check | WCAG AA/AAA 통과 확인 |

## 6. 용어를 쓸 때의 규칙

- 한 요청에 **패턴 1–2개**만 쓴다. 다섯 개를 한꺼번에 지시하면 아무것도 제대로 안 된다.
- 파라미터를 숫자로 준다 (`60ms`, `0.35`, `92vh`, `0.3 threshold`).
- 결과가 어색하면 용어를 바꿔 지시한다("부드럽게" 금지).
- "요즘 유행하는", "모던하게" 같은 표현은 지시가 아니다. 톤은 `Visual Direction` 문서에서 한 번만
  정하고, 이후에는 용어로만 말한다.
