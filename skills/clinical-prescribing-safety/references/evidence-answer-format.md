# Evidence Answer Format (OpenEvidence-style)

Read this when the task is a **clinical question** rather than a full prescription
note — "is X effective for Y", "what does the evidence say about stopping Z",
"first-line for this patient". It governs *how the answer is written and cited*;
the safety, dosing, and hard-boundary sections in `SKILL.md` still apply and still
come first.

The model to imitate is an evidence engine: **bottom line first, every claim
graded and cited, consensus and conflict made explicit, references listed with
their access level.**

## 1. Retrieve before answering

A clinical answer without a retrievable source is a guess. Anchor it:

```bash
# Regulatory label anchor (US FDA labeling via openFDA) — indication, dose,
# contraindications, boxed warning, interactions, special populations
python3 scripts/fetch_drug_label.py metformin --section contraindications --section drug_interactions

# Same, for the WHOLE core label, to quote and cite
python3 scripts/fetch_drug_label.py apixaban --max-chars 0

# Trial/review evidence and guideline-background literature
python3 <academic-research-writing>/scripts/retrieve_pubmed.py "apixaban elderly AF dosing" --retmax 15
python3 <academic-research-writing>/scripts/search_sources.py "DOAC renal impairment dosing" --years 5
```

Source ladder for a clinical claim (top = strongest anchor):

1. **Regulatory label / SmPC** — openFDA (`fetch_drug_label.py`), DailyMed, and
   the **MFDS/식약처** product page for a Korea-context patient.
2. **Societal guideline** — KDIGO, ESC/ACC/AHA, GOLD/GINA, ADA, IDSA, NICE, and
   Korean societies. Cite the *version and year*; guidelines are superseded.
3. **Systematic review / meta-analysis / pivotal RCT** — for the specific
   indication and population.
4. **Observational / registry** — label it as such; weaker for causality.
5. **Compendium (UpToDate, Lexicomp, BNF)** — practical dosing/interaction
   support; cite with its revision date.

An **AI output is never a source.** If a model (including this one) suggested the
therapy, disclose it and verify against the label/guideline before it enters the
answer.

## 2. Answer structure

1. **Bottom line** — 1–3 sentences: what to do (or not do), for whom, with the
   recommendation standing (`strong` / `conditional`) and the evidence grade.
2. **Evidence** — bullets, each claim carrying `[n]` plus its design and quality:
   label, guideline class/level (e.g. ESC I/A, KDIGO 1A), or GRADE (high → very
   low), or RCT/meta-analysis/observational.
3. **Consensus vs. conflict** — where sources agree; where they diverge and why
   (different endpoint, population, era, sponsor). Never flatten a real conflict
   into false certainty.
4. **Applicability to this patient** — individualization; **label indication vs
   off-label**; guideline and label divergence; what the source population did
   *not* include (e.g. dialysis, pregnancy, extremes of age).
5. **Safety and monitoring** — link to `assets/medication-safety-checklist.md`;
   the one or two parameters that decide whether to continue.
6. **References** — numbered; every `[n]` defined once with identifier (PMID / DOI
   / guideline URL / openFDA `set_id`) and **access level**.
7. **Uncertainty** — `[needs input]` gaps the answer depends on.

Template: `assets/clinical-evidence-answer-template.md`.

## 3. Grading vocabulary

- Use a grade **only** if a source actually assigns one. Never invent a class.
- Keep **strength of evidence** (quality) separate from **strength of
  recommendation** (guideline class). A Class I recommendation on low-quality
  evidence is common — say both.
- Hedge when the evidence is indirect: different population, surrogate endpoint,
  post-hoc subgroup, short follow-up.
- Say when the honest answer is **"do not prescribe"**, "no evidence either way",
  or "refer".

## 4. Citation rules

- One marker = one source, defined in References; markers must cover the whole
  answer, not just the first line.
- Cite the **primary source**, not a review that mentions it, for an effect size.
- Record access level; an abstract-only claim is written as such.
- Never cite a label section that is absent from the API response as evidence that
  a warning does not exist — absence in the response is not a negative finding.
- openFDA is **US labeling**; for a Korea-context patient, confirm the MFDS product
  label as well and cite it.

## 5. Anti-patterns

- **Bottom-line burying** — the recommendation appearing only in the last
  paragraph.
- **Grade inflation** — calling a single small observational study "strong".
- **Guideline laundering** — present-tense "guidelines recommend" for a superseded
  version.
- **Silent off-label** — an off-label use written as if it were labelled.
- **No-source certainty** — a confident recommendation with no `[n]` behind it.
