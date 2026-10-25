---
name: paper-review
description: >
  Review an already-written manuscript package — the paper, its table set, its figure set and its
  presentation deck — against a reviewer's checklist and return a severity-ranked report with
  line-anchored fixes. Covers AI-writing tells, number-dump paragraphs, verbosity, argument flow,
  reference/table/figure numbering and in-text placement, tone and overclaiming, and how much of the
  paper's core content the deck actually carries. Use when auditing a draft before submission, not
  when writing one. KO: 논문 검토, 원고 검토, 투고 전 점검, 논문 리뷰, 리뷰 리포트, 심사 관점 점검,
  표·그림 넘버링 점검, 발표자료 검토, AI 티, 단정적 어투. EN: review my manuscript, pre-submission
  check, manuscript audit, critique my draft, deck coverage check.
  Not for producing a manuscript (academic-research-writing), not for deck visual design
  (design-craft / deck-craft), not for copywriting (copy-craft).
---

# paper-review

Audit a finished manuscript package and report what a reviewer would actually object to, in the
order that decides the decision.

```
paper.md ─┐
tables/   ├─► ① intake ─► ② prose ─► ③ argument ─► ④ numbering ─► ⑤ deck ─► ⑥ report
figures/  │                                                                  (HIGH/MED/LOW)
deck      ┘
```

## Precedence — who owns what

- **Producing** a manuscript → `academic-research-writing`. This skill never drafts, never searches
  literature, never writes a new section.
- **Deck visual design / format** → `design-craft` + `deck-craft`. This skill only judges whether
  the deck's **content** covers the paper. Load design-craft when the user asks about looks.
- **Everyday copy tone** → `copy-craft`. This skill's tone pass is about scientific hedging and
  overclaiming, not advertising.

## When this applies / does not apply

- Use for: 투고 전 원고 점검, 심사자 관점 리뷰, 표·그림 정합성 점검, 학회 발표자료 내용 검토.
- Do not use for: writing, literature search, statistical re-analysis, journal formatting compliance
  (that is the journal's own checklist), or reviewing **someone else's** paper for a journal as a
  formal peer reviewer — the tone there is a decision letter, not a self-audit.

## Step 1 — Intake (never skip)

Collect and confirm, in one message, not five:

1. **Files** — paper (md/docx/pdf-txt), table collection, figure collection, deck. Missing piece =
   say which pass is skipped, do not silently drop it.
2. **One SSOT** — if two manuscript copies exist, ask which is live. Auditing a stale copy is the
   most expensive possible mistake here.
3. **Language and target** — Korean or English body, journal/society, manuscript type (original /
   review / case / technical note). Sets which conventions the numbering pass enforces.
4. **Deck purpose** — 학회 발표 / 저널클럽 / 그랜드라운드 / 교안. Decides what "핵심 내용" means.

Write the inventory down before reviewing. Every finding later must name which file and where.

## Step 2 — Prose pass (AI 티 · 숫자 나열 · verbose · 톤)

```bash
python3 ~/.config/opencode/skills/paper-review/scripts/prose_lint.py paper.md --lang ko
```

The script reports per line: AI-tell patterns, overclaiming/단정적 어투, number-dump sentences,
over-long sentences, hedge imbalance, connector repetition. Then **read the flagged lines yourself**
— the script counts, it does not judge. A pattern that is scientifically correct stays, and you say
why you kept it.

Four judgements to make, in this order:

1. **AI 티** — inflated significance, formulaic transitions, empty summarising ("이를 통해 ~을
   확인할 수 있었다"), tricolon padding, "매우/다양한/주요한" filler. Fix by deleting, not by
   synonym-swapping: a swapped word keeps the same hollow shape.
2. **숫자 나열** — a paragraph that becomes a list of coefficients with no verb of interpretation.
   Keep the numbers, add the sentence that says what they mean, and push the rest into a table.
3. **verbose** — one claim per paragraph; cut sentences that restate the heading or preview what the
   next paragraph will say. Target: every paragraph's first sentence carries information.
4. **톤과 단정** — `입증되었다`, `증명되었다`, `명백히`, `반드시`, `최초로` and their English twins
   (`proves`, `clearly demonstrates`, `definitively`) must be downgraded to what the design supports
   (`associated with`, `suggests`, `is consistent with`). Equally, flag **over-hedging**: a result
   buried under three qualifiers reads as if the authors do not believe it.

Detail and the full pattern/word lists: `references/prose-ai-tells.md`.

## Step 3 — Argument pass (논지 전개)

```bash
python3 ~/.config/opencode/skills/paper-review/scripts/claim_chain.py paper.md --design auto
```

Maps every result claim in Abstract/Conclusion to the Results sentence that supports it, and
raises three flags: `UNSUPPORTED` (no evidence sentence), `causal!` (causal verb behind an
observational design), and "대안 가설 언급 없음" (an observational paper with no confounding or
bias discussion). The mapping is lexical, so **read both sentences** before reporting.

Then do what no script can — the chain itself:

- **뒤집기 검사** — would the opposite data support the same conclusion? Then the evidence is not
  evidence.
- **사슬 끊김** — turn the argument into P1 → P2 → … → C and ask at each link what premise is
  missing: a definition, a citation, or data. Each sentence being true is not a chain.
- **대안 가설** — list the three a reviewer would raise (제3변수, 역인과, 선택편향) and check the
  Discussion *excludes* them, not merely mentions them.
- **Question closure** — the Introduction's stated question must be answered explicitly in the
  Discussion, in the same words. "We studied X" is not an answer to "so what".

Output one numbered list: claim → where supported → the missing link. Do not rewrite the paper
here. Rubric, fallacy table and report wording: `references/argument-logic.md`.

## Step 4 — Numbering pass (레퍼런스 · 표 · 그림)

```bash
python3 ~/.config/opencode/skills/paper-review/scripts/numbering_audit.py paper.md \
  --captions-dir tables/ --captions-dir figures/
```

Fails loudly on: a table/figure defined but never cited, cited but never defined, duplicate
numbers, gaps, and **out-of-order first citation** (Table 2 first appearing before Table 1).
Then check by eye what a script cannot:

- Placement — the citation sits in the paragraph that discusses the item, immediately after the
  first mention, not at the end of a section.
- Self-containment — the caption states n, the statistic, and the unit without the body text.
- Reference numbering — sequential by first appearance, no orphan bracket, and every `[n]` resolves
  to a real entry. Numbers referenced in the deck must match the paper's.
- Consistency across sets — `Table 1` in the paper is `Table 1` in the table collection, same order.

Rules and the common breakages: `references/numbering-rules.md`.

## Step 5 — Deck pass (내용 완전성)

```bash
python3 ~/.config/opencode/skills/paper-review/scripts/deck_coverage.py \
  --manuscript paper.md --deck deck.md
```

Prints a coverage matrix: each core claim of the paper (abstract claims + numeric results), whether
the deck carries it, and the best-matching slide. Missing items are the finding; a deck that carries
every claim is also a finding — it means the deck is a paper on slides.

Judge three things the script cannot:

- **Selection** — did the deck pick the paper's *decision-driving* result, not its first result?
- **Fidelity** — do the deck's numbers equal the paper's numbers? A drifted number on a slide is
  HIGH, because the audience will quote it.
- **Redundancy** — a slide that repeats the paper's abstract verbatim is wasted time, not coverage.

When the user also wants the deck's look judged, load `design-craft` + `deck-craft` and hand them
the format findings; keep content findings here so the two do not contradict.
Deck-specific rubric: `references/deck-coverage.md`.

## Step 6 — Report

Numbered list, never a wide table. Group by severity, and inside a group by location.

- **HIGH** — a reviewer would reject or major-revise over it: unsupported abstract claim, a figure
  cited but never defined, a number in the deck that contradicts the paper, an overturned causal
  claim.
- **MED** — weakens the paper but is fixable in an hour: number-dump paragraph, out-of-order figure,
  a paragraph of AI filler, an over-hedged key result.
- **LOW** — polish: connector repetition, long sentence, caption wording.

Each finding is three lines, no more:

```
[HIGH] paper.md L142 — 초록은 "independent predictor"라고 하지만 Results 는 조정 없는
단변량 OR 만 제시한다.
왜: 심사자가 가장 먼저 잡는 불일치. 근거 문장이 없다.
제안: Results 에 조정 모형을 추가하거나, 초록을 "associated with"로 내린다.
```

Close with: what was checked, what could not be checked and why, and the three findings that would
change the decision. Never invent a missing analysis, a citation, or a journal rule — if the paper
does not state it, the finding is "not stated", not a guess at what the authors meant.

Report format detail: `references/report-format.md`.

## Limits

- The scripts are lexical. They cannot detect a circular argument or a wrong statistic. A clean run
  is not a clean paper; the argument pass is the one that matters, and `claim_chain.py` covers only
  its vocabulary layer — chain gaps and alternative-hypothesis exclusion are read by hand.
- Korean tokenisation here is whitespace + particle stripping, not a morphological analyser. Coverage
  scores are indicative, so confirm each missing claim by reading the slide.
- PDF input must be converted to text first. Hidden-text/injection scanning belongs to the reviewer
  path for third-party manuscripts, not to your own draft.
- Reference **resolution** (does `[7]` point at the right paper) is out of scope — that is
  `academic-research-writing`'s citation verification.

## Safety

- Manuscript and reviewer material is confidential: do not upload it to gists or external services.
  Keep reports local, and never paste a full manuscript into a public URL.
- Fixes are proposals. Apply them only when the user says `--fix`-equivalent in words, and never
  apply a fix that would change a reported number.
