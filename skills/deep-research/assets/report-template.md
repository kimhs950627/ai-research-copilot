# Research deliverable templates

Two shapes. Use the short one unless the user asked for a document.

## §short — answer-first brief (default, L1 and most L2)

```
<직답 2–5문장, 인라인 [n] 포함>

## 핵심
- 
- 

## 근거
- <claim> [n] — <source, date, value>
- <claim> [n]

## 확신도 / 한계
- <what is solid, what is soft, what contradicts>
- 확인 필요: <item>
- as of <date>

## 출처
1. <title> — <url> (<type: 1차/보도/경험/추정>, <date>)
2. ...

## 다음
- <what would change the answer>
- <suggested follow-up>
```

House style: English TL;DR first (3–6 lines, same numbers and caveats), then the Korean body.
URLs as plain text so they stay clickable in Discord.

## §long — report.md (L2 only, or when a document was requested)

```
# <title>

**요약** — <3–5 bullets, each with [n]>
**As of** <date> · **범위** <scope> · **출처** <n>개 · **한계** <one line>

## 1. <question or theme, not source order>
<body with inline [n]>

## 2. ...

## 3. 불일치와 반대 증거
<where credible sources disagree, and why — population, time, measure, method>

## 4. 한계
<what the method cannot support; what remains 확인 필요>

## 5. 출처
1. <title> — <url> (<type>, <date>, access: full_text|abstract|metadata_only)

## 검증
| 축 | 점수 |
객관성/사실 정확도 · 인용 정확도 · 완전성 · 출처 품질 · 도구 효율
실행: 검색 N회 · 읽은 출처 N개 · 미해결 N건
```

Rules that apply to both shapes:

- No sentence without a source, unless it is clearly labeled inference or a gap.
- No table in the chat body (Discord does not render it) — use bullets, or put the table in the file
  and render it with `md-view`.
- Never paste raw markdown into chat; render with `md-view`.
- Scores below 0.8 on any axis must be visible in the delivery, not hidden.
