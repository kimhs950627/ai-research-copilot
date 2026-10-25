# Medical and Medical-AI Research Rules

Applies when the domain is medicine, clinical care, or medical AI. Put these at
the **front** of the skill's behavior.

## 1. Separate clinical questions from AI-method questions

Each needs different sources and different appraisal:

- **Clinical question** → guidelines, RCTs, systematic reviews, regulatory labels.
- **AI-method question** → datasets, splits, external validation, calibration,
  fairness, leakage, reproducibility.

State which kind each subquestion is, and cite accordingly.

## 2. Conservative synthesis and writing

Do not omit:

- Clinical applicability and the exact intended-use population
- **External validation** (or its absence)
- Population shift / spectrum bias between development and deployment
- **Data leakage** (patient overlap, preprocessing, label leakage)
- Limits of generalization; divergence from the trial population
- Calibration and thresholds, not discrimination alone
- Regulatory status (approved / cleared / research-use-only)

## 3. Claim–evidence verification (medical phrases)

These phrases require a **direct** supporting source, or must be softened/removed:

"latest", "state-of-the-art", "superior", "clinically useful",
"replaces existing method", "safe", "effective", "validated".

## 4. Original research / reporting

- Use only supplied data and actually executed analyses.
- Never invent participants, sample sizes, results, methods, ethics approvals, or
  registration numbers. Mark missing items `[needs input]` / `[needs analysis]`.
- Record hypothesized vs actually-performed analyses; do not change the analysis
  plan after seeing results without disclosing it.
- Follow ICMJE: AI is not an author; disclose AI tool and purpose; the human
  author is accountable.

## 5. Safety boundaries

- Never let the workflow output a **patient-specific medical order** without a
  licensed clinician's review. For diagnosis/treatment/prescribing requests that
  name a real patient, use the `clinical-prescribing-safety` skill.
- Red-flag, time-critical, or life-threatening situations → advise immediate
  professional/emergency care, not a literature answer.
- Distinguish **research findings** from **clinical recommendations**.

## 6. Recommended split for a medical/AI skill set

Keep the main skill thin; move detail to references and assets:

```
academic-research-writing/
  SKILL.md
  references/  (search policy, extraction, synthesis, writing, medical rules)
  assets/      (evidence ledger schema, contracts, templates)
  scripts/     (retrieve, verify, validate)
```

Scripts must be **real** and wired to tools; naming a script does not create it.
