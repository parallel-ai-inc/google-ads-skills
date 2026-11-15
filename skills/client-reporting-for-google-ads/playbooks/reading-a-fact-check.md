# Playbook: Read a fact check, of your own narrative or of someone else's draft

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

`scripts/fact_check.py` traces every number in a report to the measured data. This playbook says what each result means and what to do about it: fix your own narrative until it passes, or tell the person exactly what is wrong in a draft someone else wrote, and how to word it right.

## When to use it

- Your own narrative came back NOT PASSED.
- The person asks you to check a report a colleague, a junior or another agency wrote (`--report-type fact-check`, then `--report`).
- A report passed and you are about to say it is right. A pass means the numbers trace; it says nothing about the reasoning.

## What to read in the output

**Your own narrative** (`fact-check.md` in the work folder): "Numbers: N found, N traced, N refused", "Dates", "Problems with the narrative", "Refused numbers" (each with its sentence, reason and place), "Warnings", and PASSED or NOT PASSED.

**A draft** (`fact-check.md` in the output folder): the first line, "Checked against the numbers for ... compared with ...", the counts, then "Contradicted by the data", "Unclear or overclaimed", "Needs data", the "Verified" table with "Matched to", and the "Caveats" table.

## Before anything else: the comparison

Read the first line. The draft's own words say what it compares against ("compared with September"). If the measured comparison is not the same, every change figure is judged against the wrong period. A whole calendar month or quarter given as `--current` is compared with the one before it; any other range with the same number of days just before it. When they differ, measure again with `--previous` and check again. The draft's current period is read from its header: if it has none, ask the person and pass `--current`. Always use a separate work folder from your own report's.

## The decisions

| Result | Group | What it means | What to do | Label |
|---|---|---|---|---|
| Traced | Verified | A number with that value exists for that measure, campaign and comparison | Read "Matched to": a coincidence also passes | Practitioner rule, printed by the check |
| Contradicted by the data | Contradicted | No number fits; the expected one is printed after "The data says" | Give the right value from that line | Practitioner rule |
| Contradicted by the data: wrong direction | Contradicted | The sentence says it rose and it fell, or the reverse | Fix the word. The figure itself may be right | Practitioner rule |
| Matches a different measure, campaign or comparison | Unclear or overclaimed | The figure is real but belongs elsewhere, such as last year's change quoted as last month's | Rewrite with the figure for what the sentence names, from the summary | Practitioner rule |
| Matches only when rounded | Unclear or overclaimed | Close, not exact | Write the exact figure, or "about" | Practitioner rule |
| A change in points written as a percent | Unclear or overclaimed | CTR or Conv. rate moved in points | Write "points" | Practitioner rule |
| No figure in the data supports it | Needs data | A target or outside figure never given to the measure step, or a made up number | Ask the person. A target: measure again with it. A CRM or sales figure: `--given`. Otherwise remove it | Practitioner rule |
| Written in words, so not checked | Needs data | "Doubled", "a third" | Write it as a figure | Practitioner rule |
| Unknown id (your narrative) | Needs data | The id is not in the numbers | Cite an id from the summary, or drop the claim | Practitioner rule |
| Caveats row "No" | Caveats | The words for the period, the comparison or the limits are missing | Add them. The check looks for words only, so read the paragraph too | Practitioner rule |
| "Problems with the narrative": CHECK THE TARGET | Refused | A target not yet confirmed | Follow `explaining-results-and-targets.md` | Practitioner rule |
| "Problems with the narrative": cites acct but not nb | Refused | Brand is an outlier | Cite the figure without brand, first | Practitioner rule |
| "Warnings": a section the playbook asks for is missing | Passes | The report type's section is absent | Add it, or say why it is left out | Practitioner rule |

Dates are counted apart from figures and never add to the verified count.

## What the check cannot see

Claims without numbers: causes, adjectives and recommendations. Judge each one against the summary yourself. "A strong month" must agree with the figures without brand and the scorecard. "Because" needs the person's confirmation. "Keep the current setup" must still hold given a paused campaign or a missed target. Put each one that fails under Unclear or overclaimed, with the summary's numbers.

## How to fix your own narrative

Cite the right id or drop the claim, and run the check again until it prints PASSED. Never edit `numbers.json`, never type a figure you worked out, and never reword only to get past the check. A refused id with a direction is fixed by the direction word, not by a new number.

## Failure modes

- **A wrong figure called "needs data".** Check: it sits under Contradicted by the data, with the right value.
- **A right figure called wrong** because the comparison was a different period. Check: the first line, every time.
- **Dates counted as verified figures.** Check: the dates line, apart.
- **A pass presented as approval.** Check: you judged every claim without a number.
- **The draft's period guessed.** Check: the header gave it, or the person did.

## Worked example

The sample draft for Northside Plumbing, October 2026, compared with September (`examples/output/client-reporting/fact-check/`): 9 figures, 4 verified, 3 contradicted, 1 unclear, 1 needs data, and 4 dates that match.

- Contradicted: "cost per conversion rose 5.2%": it fell 5.2%. "Cost down 18%" for Drain Cleaning | Search: the data says down 37.8%, and the campaign was paused, not declining. "9.4x": Conv. value / cost was 9.09.
- Unclear: Water Heaters "fell 26.4% month over month": 26.4% is the change against last year; against September conversions fell 34.1%.
- Needs data: "the 40.00 target", because the check was measured without targets. Measured again with `--target-cpa 40`, it verifies.
- Caveats: no line on what the numbers cannot show.
- Not checkable: "October was a strong month". Without brand, cost per conversion was 25.6% above the target: an overclaim.

## What to tell the client

Usually nothing: a fact check goes to the person who wrote the draft. For them: "Four figures need correcting before this goes out. Here is each sentence and the right figure."
