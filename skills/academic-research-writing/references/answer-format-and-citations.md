# Answer Format and Citations (Perplexity-style)

Read this when the deliverable is a **direct answer to a question** rather than a
manuscript — a rapid evidence brief, a "what does the literature say about X", or
a research briefing. This is the default on-ramp to the skill; the manuscript and
PRISMA lanes in `SKILL.md` still apply when the user asks for a review or paper.

The contract has two halves: **retrieve like a search engine, answer like one too**.

## 1. Retrieve: decompose, then search every subquery

Do not answer from a single search. Perplexity-style answers come from a
decomposed query set.

1. **Decompose** the question into 2–5 atomic subqueries (population, mechanism,
   outcome, safety, comparator, recency).
2. **Route** each subquery to the right source:
   - broad web / news / policy / definitions → `websearch`, then `webfetch` the
     page that actually carries the number
   - biomedical literature → `scripts/retrieve_pubmed.py` (PubMed) and
     `scripts/search_sources.py` (Europe PMC + OpenAlex)
   - one known DOI → `scripts/verify_reference_metadata.py` (Crossref)
3. **Deduplicate** by DOI/PMID before reading.
4. **Read** at least the abstract of every source you will cite, and record the
   access level (`full_text` | `abstract` | `metadata_only`).
5. **Iterate once** only if a subquery is still unanswered; name the gap first.

```bash
# PubMed (MEDLINE) candidate records
python3 scripts/retrieve_pubmed.py "SGLT2 inhibitor heart failure" --retmax 15

# Europe PMC + OpenAlex in one pass, last 5 years
python3 scripts/search_sources.py "SGLT2 inhibitor heart failure" --years 5 --limit 10

# verify one DOI's metadata before citing it
python3 scripts/verify_reference_metadata.py 10.1056/NEJMoa2034577
```

Log the exact query string and the date you ran it. Snippets and result previews
are **discovery aids** — they never establish a result.

## 2. Answer: answer-first, every claim cited

Write the answer before the essay. The reader must be able to stop after the first
paragraph and still have the answer.

1. **Answer** — 2–5 sentences that directly answer the question. Every sentence
   that states a fact carries an inline marker `[n]`.
2. **Key points** — 3–6 bullets, each a citable claim with `[n]`, not a restatement
   of the question.
3. **Evidence detail** — grouped by theme, not by paper. Put the *numbers* here:
   effect estimate, interval, n, population, follow-up, design. Say when studies
   disagree and why.
4. **Confidence and caveats** — evidence strength (GRADE-like or your own
   `high/moderate/low`), how direct the evidence is, and what would change the
   answer. Distinguish association from causation, statistical from practical
   significance.
5. **Sources** — a numbered list where `[n]` is defined once:
   `[n] Authors (Year). Title. Journal. doi:… / URL. access: full_text|abstract|metadata_only.`
6. **Suggested follow-ups** — 2–3 next questions the reader plausibly wants,
   phrased as queries you could actually run. Never invent one whose answer you
   would not be able to ground.

Template: `assets/answer-brief-template.md`.

## 3. Citation rules (the part that makes it trustworthy)

- One `[n]` marker = exactly one source, and `[n]` appears in the Sources list.
- **Never cite a source you did not read** for the specific claim. Title-only and
  abstract-only sources get `metadata_only` / `abstract` and hedge accordingly.
- Mark the source kind: **primary study** vs **systematic review** vs **guideline**
  vs **guideline/label**. A review summarizes; cite the primary for the effect size.
- Recency matters: state the publication year in the evidence detail and prefer
  the newer study when two conflict, unless the older one is the pivotal trial.
- Prefer higher tiers first: peer-reviewed > guideline > systematic review >
  preprint (label non-peer-reviewed) > expert commentary/news (context only).
- Never write "studies show", "research suggests", or "it is known" without a
  marker. Never recycle one marker across claims it does not support.
- A claim you cannot ground is written as `[needs input]` or `[needs analysis]`,
  not softened into vague prose.

## 4. Anti-patterns

- **Citation dump** — long Sources list with only the first paragraph actually
  cited. Markers must cover the whole answer.
- **Snippet-as-evidence** — treating a search snippet or an abstract teaser as the
  result. Read the abstract at minimum; mark it as such.
- **Follow-up theater** — suggested questions you cannot answer from retrievable
  sources.
- **Silent recency error** — presenting a superseded guideline as current.
- **Source laundering** — citing a news article for a trial that the news article
  cites; go to the trial.
