---
name: deep-research
description: >
  Answer research questions the way a production deep-research system does: classify effort, write a
  brief, build a verifiable checklist, retrieve wide-then-narrow, bind every claim to a source, then
  run a separate citation pass and a rubric self-check. Covers everyday research (product, price,
  news, policy, travel, real estate, trends) and routes scholarly work to academic-research-writing.
  KO: 조사해줘, 알아봐줘, 리서치, 자료 조사, 비교해줘, 어느 게 나아, 사실 확인, 팩트체크, 최신 동향,
  근거 찾아, 출처 달아서, 검색해서 정리. EN: research this, look into, compare, fact-check, find sources.
when_to_use: >
  Trigger when the user asks for an answer that needs evidence from outside the conversation —
  a recommendation, a comparison, a price or specification, a current-events claim, a policy or
  guideline lookup, or a "is this true" check. Priority: clinical prescribing/dosing → load
  clinical-prescribing-safety FIRST; manuscript, systematic review, PRISMA, literature review →
  academic-research-writing; everything else that is a research question → this skill.
  위내시경·상부위장관·위암 검진·헬리코박터 질문이면 이 스킬이든 academic 이든 §4a(한국·일본 가이드라인 우선)를 적용한다.
license: MIT
metadata:
  author: kimaki-house
  version: "1.0"
---

# Deep Research (L1 / L2 only)

Production research systems converge on one skeleton: **classify effort → brief → verifiable outline →
wide-then-narrow retrieval → evidence binding → one-shot writing → separate citation pass → rubric gate**.
This skill is that skeleton without subagents, sized so a normal question does not cost 15× a chat.

**Prime directive: never claim more than the evidence supports.** Every material sentence traces to a
source you actually read, or it is marked `확인 필요`.

## 0. Token contract — read before searching

Research is the most expensive thing an agent does. Anthropic measured ~4× chat tokens for a single
research agent and ~15× for multi-agent; token usage alone explained 80% of BrowseComp variance. We
take the quality-per-token win and skip the parallelism.

1. **Effort first.** Pick L1 or L2 in one line and stay inside its budget. Do not upgrade silently.
2. **Search ≤ budget.** L1 3 searches, L2 10. One query per intent — rephrase at most once.
3. **Read top 5 only.** One search returns many hits; open the 3–5 that can carry the claim.
4. **One full-text fetch per source.** Then `grep -n` + `sed -n 'A,Bp'` for the section you need.
   Never paste a whole page into context.
5. **No files for L1.** L1 answers in chat. Files only for L2 or when the user asks for a document.
6. **No re-verification loops.** The citation pass runs once. A failed claim is qualified or dropped,
   not researched again.

## 1. Classify — effort, not topic

| Tier | Looks like | Budget |
|---|---|---|
| **L1 lookup** | one fact, one number, one spec, one recommendation | 1–3 searches · 3–5 sources · chat answer |
| **L2 investigation** | comparison, multi-facet question, "is X true", decision with tradeoffs | 2–4 subqueries · 4–10 searches · 5–10 sources · files |

Also tag the lane, because it changes the source rules:

- `general` — product, price, news, policy, travel, real estate, trend, person/company. Source grading:
  `references/general-lane.md`.
- `scholarly` — study-level claims, effect sizes, guidelines. Use
  `academic-research-writing/scripts/` (`search_sources.py`, `retrieve_pubmed.py`,
  `verify_reference_metadata.py`) and its ledger schema. Do **not** copy them into this skill.
- `clinical` — anything touching prescribing, dosing, contraindication, a named patient. Load
  `clinical-prescribing-safety` first; this skill only supplies retrieval.

**Breadth queries** ("list every X in Y") are out of scope for L2 single-context. Say so, offer to run
it as several L2 passes, or narrow the field with the user.

## 2. Brief — the north star

L1: three inline lines (question, scope, what counts as done). No file.
L2: write `research/<slug>/brief.md` from `assets/brief-template.md` — question, subquestions, time
scope (**as-of date, never "current"**), audience, include/exclude, done criteria.

Ask **one** clarifying question only if the answer changes the report. Otherwise state the assumption
in one line and proceed.

## 3. Outline — a verifiable checklist

L2 only. Items × fields, e.g. `요금제 × {가격, 약정, 데이터, 해지위약금, 출처}`. Each item must be
answerable by a search and each field must be fillable or explicitly marked `확인 필요`. An outline
whose cells cannot be verified is a bad outline — fix it before searching.

This is the human gate: show the outline in one short block and, when the user is present, let them
add items or fields before the expensive phase.

## 4. Retrieve — wide, then narrow

1. Start with 1–2 **broad** queries to see the landscape. Narrow queries first return nothing.
2. Then one query per subquestion. Prefer exact identifiers (model number, statute name, ticker,
   Korean official term) over adjectives.
3. Ladder: `websearch` → `search-links` (`--naver` for Korean everyday topics only) → `webfetch` →
   `browser-control` when a page is a JS shell, a login wall, or a bot block. Record which rung
   produced a load-bearing source.
4. **Source quality beats ranking.** Exclude content farms, affiliate listicles, and press-release
   rewrites when a primary document exists (official notice, filing, spec sheet, statute, dataset).
   This is the single most common production failure, found by human review, not by evals.
5. Actively look for the **counter-case**: a null result, a contradicting figure, a later revision.
6. **Region-first source selection** — for some topics the right source is regional, not global. See §4a.

## 4a. Region-first rule — 위내시경이면 한국·일본 (2026-10-21)

사용자 규칙. 질문이 **위내시경 / 상부위장관 내시경 / 위암 검진 / *H. pylori* / 위 점막병변 / ESD** 에 닿으면
**한국·일본 가이드라인을 1차 근거**로 검색·인용하고, ASGE·ESGE·AGA·ACG 는 보조로만 쓴다. 한국·일본은 위암
발생률·*H. pylori* 유병률·국가검진 체계가 서구와 달라 서구 권고를 그대로 적용하면 대상·주기·적응증이 어긋난다.

1. 순서: 한국(국가암검진 위암 검진 권고안 · 대한소화기내시경학회 · 대한위암학회 · Helicobacter 연구학회)
   → 일본(JGES · JGCA · Kyoto 분류) → 서구(한·일 근거가 없거나 주제가 서구 기원일 때만, 그 이유를 한 줄 밝힘).
2. 한·일 권고가 갈리면 **양쪽 병기** + 차이의 근거. 한쪽으로 임의 통합 금지.
3. 판번호·개정 연도는 **기억으로 쓰지 않는다** — 학회 공식 최신판 확인 후 인용.
4. 검색은 한국어·일본어 원어 쿼리를 먼저 돌린다(`위내시경 진정 가이드라인`, `上部消化管内視鏡 ガイドライン`).
   국가 문서는 학술 DB에 없을 수 있다 → `webfetch` 로 원문.

학회·학회지 경로와 PubMed 검색식은 복사하지 않고 `academic-research-writing/references/guideline-priority-kr-jp-endoscopy.md`
를 그대로 읽어 따른다(SSOT 하나).

## 5. Evidence audit

Bind claims as you go — not after writing.

- L1: keep a scratch list of `claim → url → what it says`. Never cite a hit you did not open.
- L2: `research/<slug>/ledger.json`, one row per material claim: claim · source id · url · access
  level (`full_text|abstract|metadata_only`) · location (section/table/page) · quoted excerpt ·
  value+unit+date · `support_status` (`direct|partial|conflicting|unsupported`). Validate with
  `academic-research-writing/scripts/validate_evidence_ledger.py` when the schema is reused.
- Prune: if a source does not support a cell in the outline, it does not enter the ledger. Noisy
  context is what makes long research rot.

## 6. Stop criteria

Stop when every outline cell is `filled`, `확인 필요`, or `not applicable`, or when the tier budget is
spent. Then either deliver, or report a labeled partial. "Exhaustive" and "comprehensive" are claims
that require a method you did not run — do not use them.

## 7. Write — one shot

Synthesize once from brief + ledger. Never draft sections separately and stitch them; in production
that produced reports that read as disjoint fragments.

Default deliverable is the **answer-first brief** (`assets/report-template.md` §short):

1. direct answer, 2–5 sentences
2. key points
3. evidence, with inline `[n]`
4. confidence and caveats
5. numbered sources
6. what would change the answer / suggested follow-ups

Only produce a full `report.md` when the user asked for a document, or L2 with multiple sections.

## 8. Citation pass — separate step, once

Re-read the draft against the ledger, not against memory:

- every factual sentence carries `[n]` that resolves to a source you opened;
- numbers, units, denominators, and **dates** match the source exactly;
- "latest / best / proven / safe" has direct support or gets qualified;
- each URL still resolves and points at the claimed content (title match, not just 200 OK).

Failed claim → delete, qualify, or mark `확인 필요`. Never quietly replace it with model knowledge.

## 9. Rubric gate

Score yourself 0–1 on the five axes production teams use, and fix anything below 0.8 before sending:

- **factual accuracy** — claims match sources
- **citation accuracy** — cited source supports the attached claim
- **completeness** — every asked aspect answered or explicitly marked
- **source quality** — primary over secondary, no farms
- **tool efficiency** — stayed inside the tier budget

For L1 this is a silent 3-line check. For L2, put the score line at the end of the deliverable.

## 10. Deliver

- L1: chat answer, English TL;DR then body per house style, numbered sources as plain URLs.
- L2: `research/<slug>/{brief,outline,sources,ledger,report}.md|json`, render with
  `md-view <file.md>` (gist) or `--pdf` for attachment. Never dump raw markdown into chat.
- Always state: tier used, searches run, sources read, and what remains unresolved.

## Cross-skill boundaries

- Clinical prescribing, dosing, interactions → `clinical-prescribing-safety` owns the answer.
- Manuscript, systematic review, PRISMA, meta-analysis, literature review document →
  `academic-research-writing` owns the document; this skill may still run the retrieval.
- Market demand, persona, keyword research → `market-scout`.
- Prices and purchase → `deal-scout`; hotels → `hotel-search`; trips → `trip-plan`.
- Code questions → `coding-principles`, not research.

## Files

- `references/protocol.md` — the nine steps with worked detail and failure modes
- `references/general-lane.md` — source grading, cross-checking, date discipline for non-scholarly work
- `assets/brief-template.md`
- `assets/report-template.md`
- Reused, not copied: `academic-research-writing/scripts/*`, `search-links`, `md-view`,
  `docs/browser-ladder.md`
