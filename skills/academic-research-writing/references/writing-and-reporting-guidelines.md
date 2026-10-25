# Writing and Reporting Guidelines

## Sentence → evidence discipline

Write the sentence **and** its ledger link together. If you cannot link a material
sentence to a `direct`/`partial` entry, rewrite it, qualify it, or mark
`[needs input]`.

Order within a paragraph: **core claim → evidence → interpretation → limitations**.

## Proportional language

- Reserve "demonstrates / establishes / proves" for strong, direct, consistent
  evidence; otherwise "suggests / is consistent with / may".
- "Latest / superior / clinically useful / replaces existing method" require
  direct comparative evidence — never assume.
- Report effect sizes with intervals and units, not significance stars alone.
- Keep caveats when shortening. Do not drop a qualifying clause to sound cleaner.

## Structure by document type

- **Rapid evidence brief**: question → bottom-line → key evidence table → caveats →
  references.
- **Narrative review**: intro & scope → thematic sections → what is established →
  controversies/gaps → implications.
- **Systematic/scoping review**: PRISMA-aligned — protocol, methods (search,
  screening, extraction, appraisal), results (flow, characteristics, synthesis),
  discussion, limitations.
- **Original manuscript**: IMRaD — Introduction, Methods, Results, Discussion
  (+ abstract, title, limitations, conclusions).
- **Technical/clinical/policy report**: context → question → evidence →
  options → recommendation with strength → implementation → limitations →
  references.

## Reporting standards (use when applicable)

CONSORT (trials) · STROBE (observational) · PRISMA 2020 (reviews) · TRIPOD-AI
(prediction models) · STARD (diagnostic accuracy) · CARE (case reports) ·
SPIRIT (protocols).

## Tables and figures

- One idea per table; state units in headers; define abbreviations and denominators.
- Ensure text, tables, figures, and abstract report **the same numbers**.
- Do not present a derived value without showing the inputs.

## Integrity

- Every reference verified for existence and accuracy (`scripts/verify_reference_metadata.py`).
- Every citation checked for claim support.
- Disclose AI use where the venue requires it; AI is never an author; the human
  author is responsible for accuracy.

## Final verification pass (checklist)

1. Every claim has a ledger entry; failing ones removed/qualified/flagged.
2. Numbers, units, denominators, intervals, time points match across the document.
3. No unsupported generalization; contradictory evidence acknowledged.
4. Access limits respected (no "full text" voice for abstract-only sources).
5. Scope and limitations stated; exhaustive coverage not overclaimed.
6. Confidentiality, attribution, AI-disclosure handled.
