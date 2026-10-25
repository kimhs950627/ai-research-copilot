# 디자인 시스템 · 토큰 · 데이터 분리

## 1. 왜 데이터를 UI보다 먼저 만드는가

상향식(데이터 → 카드 → 그리드 → 섹션 → 페이지) 조립의 목적은 **수정 비용**이다. 카드 단위에서
잡은 문제는 카드만 고치면 되지만, 페이지를 먼저 만들고 나중에 고치면 전체를 다시 만진다.

데이터/UI 분리(decoupling)의 규칙은 하나다: **텍스트·이미지 경로·스펙은 컴포넌트 코드에 없다.**

```js
// ✗ 하드코딩
<Card title="Linear Pendant 1200" price="₩420,000" img="/img/p1-day.png" />

// ✓ 데이터 계층
// data/products.js
export const products = [
  { id: "lin-1200", name: "Linear Pendant 1200", type: "Suspended",
    install: "Ceiling", kelvin: 3800, price: 420000,
    imageDay: "/img/lin-1200-day.webp", imageNight: "/img/lin-1200-night.webp" },
];
// ProductCard.jsx
<Card {...product} media={theme === "night" ? product.imageNight : product.imageDay} />
```

- 문구·이미지가 바뀌면 데이터 파일만 수정한다.
- `content` 데이터에서는 **텍스트 위계 자체가 레이아웃 결정 근거**가 된다. `level: 1` 은 히어로,
  `level: 3` 은 캡션 — 컴포넌트는 위계를 보고 스타일을 고른다.

## 2. 토큰 스케일 설계

토큰은 "값을 한 곳에 둔다"가 아니라 **단계를 만든다**는 뜻이다.

```
색     : surface-0/1/2, text-1/2/3, accent, accent-quiet, border, positive, negative, warning
간격   : 4 기반 — 1(4) 2(8) 3(12) 4(16) 6(24) 8(32) 12(48) 16(64) 24(96) 32(128)
타입   : display / h1 / h2 / h3 / body / small / mono, 각각 size·line-height·tracking·weight
반경   : sm(2) md(6) full(999)  ← 3단계면 충분. 균일 radius 는 AI 티
그림자 : none / hairline(1px border) / lift(작은 y) / overlay(모달)
모션   : fast(150ms) base(250ms) slow(500ms), ease-out-expo / ease-standard
z      : base / sticky / overlay / modal / toast
```

- 반경·그림자를 **줄이는** 결정이 퀄리티를 올리는 경우가 많다. 보더 1px + 배경 대비가 그림자보다
  세련되다.
- 간격 토큰을 안 쓰고 16/24 를 반복하면 리듬이 사라진다. 큰 값(96/128)을 실제로 쓴다.
- 다크/라이트를 색 토큰 재정의로만 처리하면 새 컴포넌트에 자동 적용된다. **단계형 테마**(4단계 블렌딩
  같은)도 같은 방식으로 확장한다.

템플릿: `assets/design-tokens.template.css`.

## 3. 다단계 테마 (낮/밤 블렌딩)

다크/라이트 이분법 대신 시간대 토큰 세트를 만들고 보간한다.

```js
// 4단계: 12시(낮 100%) 16시(낮 75+밤 25) 20시(낮 25+밤 75) 24시(밤 100%)
const mix = { day: 1, night: 0 };                // 시간에 따라 0~1
// 이미지: 두 컷을 겹치고 opacity 로 블렌딩
// <img class="day" style="opacity:@mix.day"> <img class="night" style="opacity:@mix.night">
// 배경: --surface-0 도 같은 비율로 보간 → 이미지 경계면이 사라진다
```

핵심: **이미지의 배경색과 웹 배경 토큰을 같은 값으로 맞춘다.** 이걸 안 하면 이미지 사각형 경계가
보여서 "붙인 그림"처럼 보인다.

## 4. 스타터킷 — 빠른 완성의 실제 조건

영상의 "1시간 완성"은 사전 스타터킷이 있어서 가능했다. 이 스킬에서 그 역할을 하는 것:

| 구성 | 이 스킬에서 |
|---|---|
| 기본 원자 컴포넌트 (LineGrid, Container, Button) | `assets/design-tokens.template.css` 로 시작, 원자 3–5개 먼저 |
| 문서 템플릿 3종 | `assets/*.template.md` |
| Taxonomy 사전 | `references/design-taxonomy.md` |
| 이미지 프롬프트 템플릿 | `assets/image-prompt.template.md` |
| 컴포넌트 카탈로그 뷰 | 아래 참고 |

## 5. 컴포넌트 카탈로그 (Storybook 대안)

Storybook 은 강력하지만 세팅 비용이 있다. 없으면 **단일 HTML 카탈로그**로 대체한다.

- `catalog.html` 하나에 토큰 스와치(색·타입·간격), 원자, 카드, 섹션을 순서대로 렌더.
- 문서 3종과 데이터 JSON 도 같은 페이지에 링크해 "한 화면에서 검증"한다.
- 그 용도는 디자인 시스템 가이드와 같다: Figma 없이 브라우저가 검증 화면이 된다.
- React 프로젝트라면 Storybook 을 그대로 써도 된다. 선택 기준은 세팅 시간 vs 프로젝트 수명이다.

## 6. 파일 구조 권장

```
src/
  styles/tokens.css         ← 유일한 값 정의처
  styles/base.css
  components/atoms/         ← Button, LineGrid, Container
  components/molecules/     ← ProductCard, SpecTable
  components/sections/      ← Hero, BrandMood, ProductGrid
  data/                     ← products.js, content.js (텍스트·이미지 경로)
  hooks/useThemePhase.js
docs/
  project-summary.md  ux-flow.md  visual-direction.md   ← 3문서는 반드시 분리
catalog.html
```

## 7. 검증

- `scripts/design-lint.py src/` 로 하드코딩 스캔. `--tokens src/styles/tokens.css` 를 주면
  토큰에 없는 hex/radius 를 "정의되지 않은 값"으로 표시한다.
- 컴포넌트에서 hex 리터럴 0건, 폰트 패밀리 리터럴 0건이 목표.
- 데이터 파일이 비어 있는 컴포넌트가 있으면 위계 설계가 빠진 것이다.

## 8. 한국어 조판 — 어절 단위로 끊는다

CSS 기본값에서 한글은 **글자 단위로 끊긴다**. "독일" 이 "독 / 일" 로 갈라지는 사고가 실제로 있었다.
`text-wrap: balance` 만으로는 해결되지 않는다 — 그건 줄 균형이고, 분절은 `word-break` 문제다.

```css
body {
  word-break: keep-all;        /* 한국어는 어절(단어) 단위로만 줄바꿈 */
  line-break: strict;          /* 줄 끝·줄 머리 금칙 처리 */
  overflow-wrap: break-word;   /* URL·영문 토큰만 예외적으로 끊김 */
  hyphens: none;
}
```

- `keep-all` 은 CJK 글자 사이의 줄바꿈을 막는다 → 한글 단어가 쪼개지지 않는다.
- `overflow-wrap: anywhere` / `word-break: break-all` 은 **한글도 쪼갠다**. 본문에 쓰지 않는다.
  (긴 URL·코드·비밀번호에만, 그 요소에만 한정해서 쓴다.)
- 제목에는 `text-wrap: balance` 를 함께 쓴다(줄 길이 균형). 둘은 경쟁하지 않는다.
- 표 셀·캡션·버튼 라벨에도 상속되므로 `body` 한 곳에 넣으면 충분하다.
- 한글이 없는 코드·숫자 열은 예외로 `font-variant-numeric: tabular-nums` 정도만 추가한다.

검증: `scripts/page-check.sh` 가 **문자별 rect 의 top 을 비교해** 어절 분절을 찾아낸다
(`한글 어절이 줄바꿈에서 쪼개짐 '독/일'`). HIGH/MED 가 0 이 될 때까지 고친다.

## 9. 마크다운 누출 금지 — 화면에 `**` 가 보이면 실패

저자는 `**굵게**` 를 자연스럽게 쓴다. HTML 로 옮길 때 변환하지 않으면 **별표가 그대로 보인다**.
실제 사고: 숙소 비교 페이지에 `**에어비앤비는 포르투에서만 이긴다**` 가 그대로 출력됐다.

- 생성기는 텍스트를 이스케이프한 뒤 **인라인 마크다운만** HTML 로 바꾼다:
  `**x**` → `<b>`, `*x*` → `<i>`, `` `x` `` → `<code>`.
- **블록 문법(`#`, `- `, `|…|`, `[]()`)은 지원하지 않는다** — 레이아웃과 데이터 구조가 이미 그 역할을
  한다. 필요하면 작성 단계에서 HTML 로 쓰거나 데이터를 나눈다.
- 카드·덱·책 생성기에는 `inline_md()` 가 내장되어 있다. 사이트·뉴스레터 생성기는 명시적 `<b>` 를 쓴다.
- 검증: `scripts/page-check.sh` 가 `<pre>/<code>/<script>/<style>` **밖의 텍스트**에서 `**`, `` ` ``,
  `[]()`, `# 제목`, `|…|` 를 찾아 HIGH/MED 로 보고한다.
  - HIGH: bold·code·link·heading / MED: italic·strike·table
- 이 검사는 카드·덱·책 페이지에도 그대로 돌릴 수 있다(독립 HTML 이므로).
