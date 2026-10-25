# Evidence Extraction

Goal: turn a source into **ledger entries** that make a specific sentence
defensible.

## Two separate verifications

1. **Source existence** — does the paper exist, with matching title, authors,
   year, journal, and DOI/PMID? (Use `scripts/verify_reference_metadata.py`.)
2. **Claim support** — does that paper actually support the claim and numbers you
   attach? Quote the exact supporting passage and its location (section, table,
   figure, page).

Never collapse (1) into (2). A valid DOI does not prove the claim.

## What to extract per material claim

- **Claim** — the exact sentence the document will make.
- **Source** — title, authors, year, journal, DOI/PMID/URL.
- **Access level** — `full_text` | `abstract` | `metadata_only`.
- **Evidence location** — e.g. `Results / Table 2 / p.8`.
- **Supporting excerpt** — verbatim, shortest text that carries the claim.
- **Study** — design, population, sample size, intervention/exposure, comparator,
  outcome definition, follow-up.
- **Result** — effect estimate, measure (RR/OR/HR/MD/%), confidence interval,
  denominator, unit.
- **Limitations** — from the paper and your appraisal.
- **support_status** — `direct` | `partial` | `conflicting` | `unsupported`.
- **verification_status** — `unverified` | `verified` | `flagged`.

## Extraction rules

- Copy numbers **exactly**: value, interval, unit, denominator, time point.
- Preserve subgroup vs overall distinctions.
- Distinguish **statistically significant** from **clinically/practically important**.
- Record **conflicting** findings as their own entries; do not average them away.
- If the text does not support the claim → `unsupported`, and fix the sentence.
- If only part is supported → `partial`, and narrow the sentence.
- Keep methods, not just results: design and population determine generalizability.

## Bias and certainty (only when actually applied)

- RCTs → Cochrane RoB 2.
- Non-randomized → ROBINS-I.
- Diagnostic studies → QUADAS-2.
- Prediction models / AI → PROBAST / TRIPOD-AI.
- Overall certainty → GRADE (only if you run it).

Do not claim a framework was used unless you applied it and can show the output.

## Medical AI extraction extras

- Data sources and splits (internal / external / temporal).
- **Leakage** risk (patient overlap, preprocessing fit on test, label leakage).
- External validation: present? on how many sites / what population shift?
- Reference standard and how it was adjudicated.
- Reporting of calibration, not only discrimination.
- Regulatory status and intended use statement.

## Handling gaps

- Missing data → `[needs input]`. Do not impute or guess.
- Inaccessible full text → record with access limit and a note, not silence.
- Conflicting evidence → keep both, describe the disagreement, do not force a
  single conclusion.
