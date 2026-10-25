# <Clinical question, stated plainly>

<date> · sources accessed: <n> · answer confidence: high | moderate | low

> Decision support only. A licensed clinician must review, confirm, and sign any
> plan. Confirm this is a clinician acting on their own patient.

## Bottom line

<1–3 sentences: the recommendation, for whom, with strength (strong/conditional)
and evidence grade. This must stand alone without the rest of the document.>

## Evidence

- <Claim> — <design + grade: guideline Class I/A, GRADE moderate, RCT n=…,
  meta-analysis of k trials> [1]
- <Claim> — <design + grade> [2]
- <Claim> — <design + grade> [3]

## Consensus vs. conflict

- **Consensus:** <what every source agrees on>
- **Conflict:** <sources that diverge> — <why: endpoint / population / era / sponsor>
- **Where this sits:** <how you resolved it, or that it stays unresolved>

## Applicability to this patient

- **Indication status:** labelled | off-label — <basis>
- **Source-population fit:** <what the trials included; what they excluded that
  this patient has/has not>
- **Individualization:** <weight, age, renal/hepatic, pregnancy, comorbidity,
  interacting meds>

## Safety and monitoring

- <Key contraindication / interaction result> — see `assets/medication-safety-checklist.md`
- **Monitor:** <parameter, how often, target, action if abnormal> [n]

## Uncertainty

- [needs input] <missing item the answer depends on>
- <what would change the recommendation>

## References

[1] <Label / guideline / study>. <identifier: PMID, DOI, URL, or openFDA set_id>.
    access: <full_text|abstract|metadata_only>
[2] <…>

<!--
Retrieval log (keep)
- <date> fetch_drug_label.py <drug> — set_id <…> — sections: <…>
- <date> retrieve_pubmed.py "<query>" — n=<…> — used: [2]
- <date> <guideline body> <version/year> — <URL> accessed <date>
-->
