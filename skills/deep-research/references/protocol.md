# Protocol detail (L1 / L2)

Nine steps, in order. Each step has the failure mode it exists to prevent. Everything here is derived
from production systems: Anthropic's orchestrator-worker research system, LangChain's Open Deep
Research, NVIDIA AI-Q, DeepResearch Bench's evaluation axes, and RhinoInsight's control mechanisms.

## 0. Classify

**Failure mode prevented:** investing ten minutes in a question that needed one call, or shipping a
one-call answer to a question that needed a comparison.

Classify on two axes.

Effort:
- **L1** — one cell of an answer. A price, a spec, a date, a yes/no, a single recommendation.
- **L2** — several cells that must agree with each other. A comparison, a decision with tradeoffs,
  a claim that requires chronology, a question with 3+ facets.

Lane:
- **general** — see `general-lane.md`.
- **scholarly** — study-level claims. Hand the retrieval to
  `academic-research-writing/scripts/search_sources.py` (Europe PMC + OpenAlex) and
  `retrieve_pubmed.py`; verify metadata with `verify_reference_metadata.py` (Crossref). Reuse its
  `assets/evidence-ledger.schema.json` instead of inventing a second ledger.
- **clinical** — load `clinical-prescribing-safety` first. Retrieval support only, never the order.

If the request is breadth ("every company in the index", "all 17 tools"), refuse the tier: an L2
single-context run will silently sample. Offer N narrow runs or a narrower field.

## 1. Brief

**Failure mode prevented:** answering a question the user did not ask, or drifting as new leads appear.

The brief is the north star for every later decision, so it must be short and falsifiable.

- Question in one sentence.
- Subquestions: 2–4, each independently answerable.
- Time scope: an explicit as-of date. "Current" is not a scope.
- Audience and use: who reads the answer and what they will do with it.
- Include / exclude: geography, product tier, population, source types.
- Done criteria: which cells filled constitutes success.

LangChain's observation is the reason briefs exist: the clarification chat is verbose and token-heavy,
so it gets compressed into a brief that the rest of the run measures against.

Ask at most one clarifying question, and only when the answer changes the shape of the report. When
the user is not present, write the assumption into the brief and proceed.

## 2. Outline as a verifiable checklist

**Failure mode prevented:** non-executable plans. An outline of topics feels productive and cannot be
checked; an outline of cells can be marked filled or missing.

RhinoInsight converts requirements into traceable sub-goals and has a critic refine them before any
searching. The ritual is cheap: write `item × fields`, then ask of every cell "which search would fill
this, and what would count as the answer".

Example:
```
요금제 3종 × {월 요금, 약정, 데이터/통화, 해지 위약금, 프로모션 종료일, 출처}
```

Cells that cannot be filled from public sources are dropped now, not fudged later.

This is the human gate. Show the outline in a short block; if the user is present, they can add items
or fields before the expensive phase. One gate, not a chain of approvals.

## 3. Retrieve

**Failure mode prevented:** long, over-specific first queries that return almost nothing; and the
opposite, endless broad browsing that never resolves.

Anthropic's system prompts encode "start wide, then narrow" precisely because agents default to narrow.

Order of operations:
1. 1–2 broad queries to map the landscape and learn the vocabulary real sources use.
2. One query per subquestion, using the vocabulary just learned plus exact identifiers.
3. Open the 3–5 hits that can carry a claim. Snippets are discovery aids, never evidence.
4. Fetch the source once; extract only the needed section.
5. If the page is a JS shell, login wall, or bot block, escalate the ladder in
   `docs/browser-ladder.md` (websearch → search-links → webfetch → CDP → Aside) and note the rung.

Deliberately search the counter-case: a later revision, a dissenting figure, a null result. Contradiction
found early is cheaper than contradiction found after drafting.

## 4. Evidence

**Failure mode prevented:** context rot — the failure RhinoInsight names, where accumulated tool output
crowds out the reasoning that made the run useful.

Bind while reading. A row per material claim: claim, source, url, access level, location, quoted
excerpt, value with unit and date, support status. Anything that does not map to an outline cell is
dropped, which is the pruning step and the main token saving.

`support_status` values:
- `direct` — source states it.
- `partial` — source supports part of the sentence (population, time, measure differs).
- `conflicting` — a credible source disagrees; both go in the answer.
- `unsupported` — no source carries it; the sentence gets `확인 필요` or is removed.

## 5. Stop

**Failure mode prevented:** unbounded loops that burn budget after the marginal source stopped adding
information.

Stop when every cell is `filled`, `확인 필요`, or `not applicable`; or when the tier budget is spent.
Then deliver, or deliver a labeled partial. Never claim exhaustive coverage without a documented
screening method.

## 6. Write, one shot

**Failure mode prevented:** disjoint reports. LangChain's earlier version wrote sections in parallel
with subagents and the report read as stitched fragments; they fixed it by restricting parallelism to
research and writing in one pass.

Compose from brief + evidence, ordered by question rather than by source. Keep established fact,
interpretation, and hypothesis visibly separate. Match certainty to evidence strength.

## 7. Citation pass

**Failure mode prevented:** citations that exist but do not support the sentence — the most common
defect in automated reports, and the one DeepResearch Bench measures as citation accuracy.

Anthropic runs this as a separate agent for a reason: it is a different task from writing. Doing it in
the writing pass hides the errors.

Check, in one pass:
- each `[n]` resolves to a source that was opened, not just listed;
- numbers, units, denominators, and dates match;
- qualifiers survived shortening;
- superlatives have direct support;
- the URL still serves the claimed content (title check, not status code).

Repair by deletion, qualification, or an explicit gap. Never by substituting model memory.

## 8. Rubric gate

Anthropic's judge rubric maps directly onto self-review, and DeepResearch Bench separates report quality
from retrieval quality (effective citation count, citation accuracy). Score both:

- report: factual accuracy, citation accuracy, completeness, readability
- retrieval: source quality (primary over secondary), tool efficiency (inside budget)

Below 0.8 on any axis → fix before sending. L1 runs this silently as three lines; L2 prints the score
line at the end so the user can see what was weak.

## 9. Deliver and persist

L2 artifacts live under `research/<slug>/`:

```
brief.md      question, scope, done criteria
outline.md    checklist with filled / 확인 필요 marks
sources.md    what was read, access level, rung
ledger.json   claim ↔ source binding
report.md     the deliverable
```

Render with `md-view` for a GitHub-rendered link, or `--pdf` for an attachment. Do not paste raw
markdown into chat.

Every delivery states: tier, searches run, sources read, unresolved items. That line is what makes the
next run cheaper — it tells the reader where the floor is.

## Failure catalogue

- Answering from model memory and decorating it with links found afterwards. Citation accuracy zero.
- Treating a search snippet as the result. Snippets are discovery aids.
- One long narrow query, no results, then declaring the topic unresearchable.
- Citing a content farm because it ranked first while the primary document sat at position 7.
- Upgrading an L1 into a report because the topic felt important.
- Presenting an abstract-only reading as if the full text was read.
- "Current" without a date, in a field where prices change monthly.
