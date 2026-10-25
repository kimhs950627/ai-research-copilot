# UX Flow — <프로젝트 이름>

> 구조와 데이터. 색·폰트는 쓰지 않는다(`visual-direction.md`).

## 1. 사용자 시나리오

1. <진입: 어디서 무엇을 보고 도착>
2. <첫 인지: 무엇을 이해>
3. <탐색: 무엇을 비교/클릭>
4. <확신: 어떤 근거를 봄>
5. <행동: 문의/가입/다운로드>

각 단계마다 **화면에 무엇이 보여야 하는지**를 한 줄로 적는다.

## 2. 사이트/앱 구조

```
<홈>
 ├─ <히어로>
 ├─ <브릿지: 브랜드 메시지>
 ├─ <그리드: 엔티티 목록>
 │    └─ <상세: /item/:id>
 ├─ <증거: 수치·후기>
 ├─ <CTA>
 └─ <푸터>
```

## 3. 데이터 스키마

```js
// entity: <Product>
{
  id: string,             // "lin-1200"
  name: string,           // 화면 표기명
  type: string,           // 분류
  installMethod: string,
  kelvin: number,         // 물리 파라미터
  specs: { width: number, material: string, ... },
  price: number,
  imageDay: string,       // "/img/lin-1200-day.webp"
  imageNight: string,
  tagline: string,
  body: string,
}
```

- 반복 엔티티: <개수>
- 이미지 세트: <낮/밤/단계형>
- 텍스트 위계: `level` 필드를 두고 컴포넌트가 스타일을 고르게 한다.

## 4. 컴포넌트 목록

| 컴포넌트 | 종류 | 역할 |
|---|---|---|
| `<Container>` | atom | 최대 폭·좌우 여백 |
| `<LineGrid>` | atom | 배경 격자 |
| `<ProductCard>` | molecule | 엔티티 1개 표현 |
| `<ProductGrid>` | section | 카드 배열 |
| `<BrandMoodPano>` | section | 브릿지 (가로 스크롤) |
| `<TimelineBar>` | molecule | 스크롤 진행 표시 |
| `<SpecTable>` | molecule | 스펙 표 |

## 5. 상태 (앱이면 필수, 정적 쇼케이스면 "해당 없음" 명시)

| 상태 | 화면 |
|---|---|
| loading | 스켈레톤 <무엇> |
| empty | <문구 + 행동 유도> |
| error | <인라인 메시지 + 재시도> |
| unauthorized | <안내 + 로그인 경로> |

## 6. 반응형 규칙

| 브레이크포인트 | 변경 |
|---|---|
| 375–639 | 1열, 히어로 텍스트 축소, 가로 스크롤 → 세로 스택 |
| 640–1023 | 2열 |
| 1024–1439 | 3열, 사이드 여백 확대 |
| 1440+ | 1200–1280 컨테이너 고정 |

## 7. 데이터/UI 분리 체크

- [ ] 컴포넌트 파일에 문자열·이미지 경로 리터럴 0건
- [ ] `data/` 에 모든 카피가 존재
- [ ] 컴포넌트는 props 로만 내용을 받는다
