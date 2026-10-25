# Deck pass — does the talk carry the paper

Read this when judging a presentation deck. Format and visual design belong to `design-craft` +
`deck-craft`; this file judges **content**.

## What "핵심 내용을 빠짐없이" means

It does **not** mean every result. A talk has 10–20 minutes; a paper has 3,000 words. The test is:

1. **Decision-driving result present?** The one finding that would change the audience's practice or
   belief. If the deck shows the first result instead of the most important one, that is HIGH — a
   common failure where the paper's Table 1 becomes slide 4.
2. **Question → answer closed?** Slide 2 must state the question; the conclusion slide must answer
   the same question in one sentence. A deck that ends on "Thank you" without the answer is MED.
3. **Every number on a slide equals the paper.** Drift is HIGH: the audience quotes slides.
4. **Methods enough to judge?** Design, n, setting, exposure/outcome, analysis — four slides' worth
   at most, but skipping design entirely makes a clinical audience distrust the result.
5. **Limitations stated at least once.** A talk with no limitation slide reads as overselling.

## Coverage matrix produced by the script

```
[MISS] 0.36  S2  This study proves that early endoscopy clearly reduces mortality...
[OK ]  0.40  S2  Early endoscopy is associated with lower mortality.
```

- Score = keyword overlap between the claim and the best slide (0–1), +0.15 when the claim's
  numbers all appear on that slide.
- `MISS` with a high score (0.35–0.45) = **paraphrased on a slide** — read the slide before
  reporting it. The tokeniser strips particles, so a rewritten sentence often scores low.
- `MISS` with 0.00 and a `-` slide = genuinely absent.
- `[숫자 누락 …]` = the slide discussing this claim lacks specific numbers. Ask whether the talk
  needed them; a qualitative claim may legitimately drop them.

## Claim selection — what counts as a core claim

Take from Abstract and Conclusion when headings exist. Typically 8–15 claims. Then triage:

- Must carry: the primary outcome, the primary comparison, the main conclusion.
- Should carry: secondary outcomes that change interpretation, the key subgroup.
- May drop: sensitivity analyses, every baseline variable, secondary endpoints that only confirm.

Report the drops you accept, and why. Silence about a dropped secondary outcome is the failure mode
— the author assumes it is covered.

## Selection vs redundancy

If coverage is 100%, the deck is a paper on slides. Flag it: a good talk **subtracts**. Look for:

- a slide that reproduces the abstract verbatim;
- a results slide with a full table the audience cannot read;
- three slides of background when the audience already knows the field.

Then report the *recommended cut*, not just a count.

## Handing off to design-craft

When the user also wants the look judged:

1. Send format findings to `design-craft` + `deck-craft` (fonts, contrast, one-claim-per-slide,
   24 pt floor, overflow, colorblind safety, AI-tell visuals).
2. Keep content findings here. Never re-report a design issue as a content issue — two reports
   disagreeing on the same slide destroy trust in both.
3. One combined verdict at the end, clearly split: **내용(paper-review) / 형식(design-craft)**.

## Audience-specific checks

- **학회 발표 (conference oral)** — conclusion ≤ 3 bullet points, no new data in the last slide.
- **저널클럽** — must include the study's weaknesses and the applicability discussion; coverage of
  the paper's limitations is mandatory, not optional.
- **그랜드라운드** — clinical takeaway per slide block; background may be longer.
- **교안 / lecture** — coverage of the paper matters less than the teaching points; judge whether
  the deck teaches the method, not whether it summarizes the paper.
