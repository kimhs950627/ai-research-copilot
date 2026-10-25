# Image prompt template — A(고정) + B(가변)

여러 이미지를 **한 세트처럼** 보이게 하는 유일한 방법은 고정부와 가변부를 분리하는 것이다.
A 는 절대 바뀌지 않고, B 만 아이템별로 바뀐다.

## A — 고정 블록 (모든 이미지 동일)

```
<재질>, <구도>, <정렬>, <여백>, <조명>, <배경>, <금지>, <카메라/스타일>
```

예시:

```
matte black anodized aluminum and white frosted glass,
front elevation view, centered, generous negative space with even margins,
soft directional studio light at 3800K from upper left,
seamless {SURFACE_TOKEN} background (exact hex in the prompt),
no props, no text, no logo, no watermark, no people,
product photography, 85mm, f/8, sharp, high dynamic range
```

규칙:

- **배경색을 CSS 토큰과 같은 값으로** 쓴다(예: `#F2EDE6`). hex 를 프롬프트에 직접 넣어야 한다.
- 구도·여백을 A 에 못박는다. 개체마다 구도가 달라지면 그리드 리듬이 깨진다.
- 카메라/조명을 고정한다. 조명이 바뀌면 다른 세트처럼 보인다.
- "no text, no logo, no watermark, no props" 를 항상 넣는다.

## B — 가변 블록 (아이템별)

```
<형태>, <치수>, <색온도/빛>, <설치 방식>, <특징>
```

예시:

```
slim linear pendant, 1200mm, warm 3800K light bar, low-profile ceiling canopy
```

## 세트 규칙

| 세트 | 컷 | 용도 |
|---|---|---|
| 낮/밤 2컷 | `-day`, `-night` | 단순 테마 전환 |
| 4단계 | 12/16/20/24시 컷 또는 2컷 블렌딩 | 단계형 테마(권장: 2컷 + opacity 보간) |
| 상태별 | 기본/호버/사용중 | 제품 인터랙션 |

- 낮 컷: 조명 꺼짐 또는 약함, 배경 밝은 토큰.
- 밤 컷: 조명 켜짐(빛 자체가 주인공), 배경 어두운 토큰.
- 두 컷의 **구도·크롭·카메라를 완전히 동일하게** 유지한다(블렌딩의 전제).

## 데이터로 내보내기

```js
export const products = [
  {
    id: "lin-1200",
    name: "Linear Pendant 1200",
    promptB: "slim linear pendant, 1200mm, warm 3800K light bar, low-profile canopy",
    imageDay:   "/img/lin-1200-day.webp",
    imageNight: "/img/lin-1200-night.webp",
    backgroundToken: "#F2EDE6",
    renderSize: { w: 1600, h: 1600 },
  },
  // ...
];
```

생성 스크립트는 `A + " " + promptB` 를 아이템마다 조립한다. 이렇게 하면 20개 아이템 프롬프트가
한 곳에서 관리되고, 세트 일관성을 나중에 검증할 수 있다.

## 검증

- [ ] 배경 hex 가 토큰 값과 정확히 일치하는가.
- [ ] 모든 컷의 구도·크롭·조명이 동일한가(썸네일을 나란히 놓고 확인).
- [ ] 텍스트/로고/워터마크/소품 0건.
- [ ] 낮/밤 컷을 겹쳐 블렌딩했을 때 어긋남이 없는가.
- [ ] webp/avif 로 변환, 크기 지정, 용량 확인(히어로 300KB 이하 목표).
