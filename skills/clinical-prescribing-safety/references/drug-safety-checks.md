# Drug Safety Checks

Run every check and **show its result** in the plan. A check with no data is
`[needs input]`, not "no interaction".

## 1. Contraindications

- **Absolute** — do not give (e.g. active GI bleed + anticoagulant; severe aortic
  stenosis + vasodilator; sulfa allergy + sulfonamide).
- **Relative** — weigh risk/benefit, document the rationale.
- Check drug-specific boxed warnings and pregnancy/lactation status.

## 2. Allergy and prior reactions

- Distinguish true allergy vs intolerance vs side effect.
- Cross-reactivity classes: penicillins/cephalosporins, sulfonamides, NSAIDs +
  aspirin (asthma/nasal polyps), iodinated contrast.
- Record the reaction type (rash, anaphylaxis) and when.

## 3. Drug–drug interactions

Screen the full med list against the new drug and against itself:

- **Pharmacokinetic**: CYP3A4/2D6/2C9/1A2/2C19 inducers/inhibitors, P-gp, OATP.
- **Pharmacodynamic**: additive QT prolongation; bleeding (anticoagulant +
  antiplatelet + NSAID/SSRI); hyperkalemia (ACEi/ARB + MRA + K-sparing +
  K supplement); CNS/respiratory depression (opioid + benzodiazepine + gabapentinoid);
  serotonin syndrome (SSRI/SNRI + MAOI/triptan/tramadol/linezolid);
  hypoglycemia (insulin/sulfonylurea + others); nephrotoxicity (NSAID + ACEi/ARB + diuretic).
- Note **timing** requirements (e.g. MAOI washout).

## 4. Duplication / therapeutic overlap

- Same class or same mechanism already present.
- Brand/generic duplicates, combination products, OTC/herbal overlap
  (e.g. acetaminophen in multiple products).

## 5. Disease-state cautions

| Condition | Think about |
|---|---|
| Asthma/COPD | β-blockers (non-selective), NSAIDs |
| Heart failure | NSAIDs, some TZDs, high-dose β-blockers |
| CKD | NSAIDs, high-dose/metformin in severe CKD, gadolinium |
| Liver disease | acetaminophen max, statin/valproate caution |
| Seizure | tramadol, bupropion, some fluoroquinolones |
| Glaucoma (closed-angle) | anticholinergics |
| BPH | anticholinergics, α-agonists |
| Long QT / bradycardia | QT-prolonging drugs, drug–drug QT stacking |

## 6. Special populations

See `special-populations.md`: pediatrics, pregnancy/lactation, older adults
(Beers criteria, frailty, polypharmacy, deprescribing), renal/hepatic impairment.

## 7. Monitoring safety

For every high-risk drug, define the **parameter, interval, target, and action**
(e.g. potassium + creatinine 1–2 weeks after ACEi start; INR per protocol;
LFTs baseline and periodic; ECG for QT risk).

## Output

A table: `check | finding | source | action required`. Any unresolved check
blocks "safe to prescribe" and must be surfaced.
