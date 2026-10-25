---
name: clinical-prescribing-safety
description: >
  Give evidence-graded, cited answers to clinical questions (bottom line first, consensus vs.
  conflict, references) and draft safe medication plans for a named patient: indication,
  contraindications, interactions, organ limits, dose adjustment, monitoring, counselling. Use
  when starting, stopping, switching or adjusting a drug, or asking what the evidence says for
  this patient. Clinical decision support only — never a substitute for a licensed clinician. KO:
  처방, 약물, 용량, 상호작용, 금기, 알레르기, 신기능, 약물 검토, 증례, 임상질문, 근거 답변.
when_to_use: >
  Trigger on prescribing, dose calculation, renal/hepatic dose adjustment, drug
  interactions, allergy or contraindication checks, medication reconciliation,
  deprescribing, an evidence-graded clinical answer, or any request that names a
  real patient and a drug. Korean triggers: 처방, 약물, 용량, 감량, 증량, 중단, 병용,
  상호작용, 금기, 알레르기, 신기능/간기능 조정, 약물 검토, 증례, 환자, 임상질문, 근거 답변,
  최신 지침, 오픈에비던스처럼.
license: MIT
metadata:
  author: command-code-skills
  version: "1.0"
---

# Clinical Prescribing Safety

Assist a clinician to prescribe **safely**. This is decision **support**, not an
autonomous prescriber.

> **Hard boundary.** Never present output as a final order for a real patient.
> A licensed clinician must review, confirm, and sign every medication plan. If
> the user is not a clinician acting on their own patient, stop and say so.

## 0. Before anything else

1. Confirm the setting: **who is the clinician, who is the patient, and is this a
   real prescription?** If unclear, ask.
2. **Red flags first.** If the request suggests an emergency (anaphylaxis,
   severe bleeding, arrhythmia with instability, sepsis, overdose, suicidal
   intent, acute chest pain/stroke signs), stop prescribing support and advise
   immediate emergency care.
3. Never fabricate patient data. Missing values are `[needs input]`.

## 1. Assemble the minimum dataset

Do not dose without these. Record what is present and flag what is missing:

- Indication and clinical goal (target outcome, time to reassess)
- Age, sex; **weight** (and height/BSA if relevant)
- Pregnancy / lactation status
- **Renal function** (eGFR or CrCl) and **hepatic function**
- Allergies and prior adverse drug reactions
- Comorbidities relevant to the drug (cardiac, respiratory, GI, psychiatric)
- **Full current medication list** including OTC, herbals, supplements
- Relevant labs (electrolytes, glucose, INR, cultures, etc.)
- Setting (outpatient / inpatient / ICU), adherence, cost/access

If a critical item is missing, state the assumption or ask — do not silently guess.

## 2. Confirm indication and evidence

- Does the diagnosis/indication match a guideline-supported use?
- Is this the recommended first-line, or a justified alternative?
- Get the **guideline/label source** for the recommendation (see
  `references/evidence-and-guideline-anchoring.md`).
- Flag **off-label** use explicitly, with its evidence basis.

## 3. Screen safety (before dosing)

Run, and show the result of, each check in
`assets/medication-safety-checklist.md`:

- **Contraindications** — absolute vs relative.
- **Allergy / cross-reactivity**.
- **Drug–drug interactions** (including CYP/transporter, QT, serotonergic,
  bleeding, hyperkalemia, CNS depression).
- **Duplication / therapeutic overlap** with current meds.
- **Disease-state cautions** (asthma/COPD, CKD, heart failure, liver disease,
  seizure, glaucoma, BPH).
- **Pregnancy/lactation** category and alternatives.
- **Special populations** (pediatric, elderly/Beers, frailty).

Details: `references/drug-safety-checks.md`, `references/special-populations.md`.

## 4. Compute the dose

- Route, formulation, strength.
- Weight-based or fixed; **per dose AND per day**; max dose.
- **Renal/hepatic adjustment**; loading dose vs maintenance.
- Calculate and state the arithmetic explicitly; use
  `scripts/` if available. Recompute rather than trusting a remembered number.
- State duration, taper, and stopping plan.

Details: `references/dosing-and-adjustment.md`.

## 5. Monitoring and follow-up

- Which parameter, how often, target range, and what to do if abnormal
  (e.g. potassium/creatinine with ACEi/ARB/MRA, INR with warfarin, glucose with
  steroids, LFTs, CBC, QT/ECG).
- When to reassess efficacy; when to escalate or stop.

## 6. Patient counselling

- How to take it, common side effects, **serious warning signs** (in plain
  language), interactions to avoid (food/alcohol/OTC), and what to do if a dose
  is missed.

## 7. Output

Produce a structured **Prescription Note** (`assets/prescription-note-template.md`)
containing: problem/indication · plan (drug, dose, route, frequency, duration) ·
the safety checks and their results · monitoring · counselling · **explicit
uncertainties** · the reviewer/approval line.

For a question rather than a full plan, use the evidence-answer format in §8.

Separate three things clearly:

1. **Guideline/label recommendation** (cited)
2. **Individualization** (why this patient)
3. **Uncertainty / gaps** (`[needs input]`)

## 8. Evidence answer (OpenEvidence-style)

When the request is a **clinical question** rather than a full prescription — "is X
effective for Y", "what is the evidence for stopping Z" — answer like an evidence
engine: bottom line first, every claim graded and cited, consensus and conflict
made explicit, references listed with their access level.

- **Bottom line** — 1–3 sentences: what to do, for whom, with strength
  (`strong`/`conditional`) and evidence grade. Stands alone.
- **Evidence** — bullets, each claim carrying `[n]` plus design/grade (label,
  guideline class, GRADE, RCT / meta-analysis / observational).
- **Consensus vs. conflict** — where sources agree, where they diverge, and why.
- **Applicability** — label vs. off-label, source-population fit, individualization.
- **References** — numbered; each with PMID / DOI / guideline URL / openFDA
  `set_id` and `access` level.

Retrieve before answering — a clinical answer without a retrievable source is a
guess:

```bash
python3 ~/.config/opencode/skills/clinical-prescribing-safety/scripts/fetch_drug_label.py metformin \
  --section contraindications --section drug_interactions   # US FDA label (openFDA)
python3 ~/.config/opencode/skills/academic-research-writing/scripts/retrieve_pubmed.py "apixaban elderly AF dosing"
```

An **AI output is never a source**, and a grade is used only if a source assigns
it. openFDA is US labeling — for a Korea-context patient also confirm the
MFDS/식약처 product label.

Full contract and command menu: `references/evidence-answer-format.md`; template:
`assets/clinical-evidence-answer-template.md`. The safety, dosing, and
hard-boundary rules above still come first.

## 9. Consistency and honesty

- Distinguish **evidence strength** from **recommendation strength**.
- If the safest action is *not* to prescribe, or to refer, say so.
- If a requested drug is contraindicated, refuse the plan and offer alternatives.
- Never invent a dose, interaction result, or lab value.

## Bundled files

- `references/drug-safety-checks.md`
- `references/dosing-and-adjustment.md`
- `references/special-populations.md`
- `references/evidence-and-guideline-anchoring.md`
- `references/evidence-answer-format.md` (OpenEvidence-style cited answer)
- `assets/medication-safety-checklist.md`
- `assets/prescription-note-template.md`
- `assets/clinical-evidence-answer-template.md`
- `scripts/fetch_drug_label.py` (openFDA label sections)
