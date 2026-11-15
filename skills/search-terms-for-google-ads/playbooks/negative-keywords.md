# Playbook: Write, test and clean up negative keywords

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

How to turn Exclude verdicts into the narrowest negatives that stop them, what to do with every negative the test rejects, and how to check negatives already in the account for conflicts. It reads what `scripts/check_negatives.py` prints and the "Negative keywords" part of the summary.

## When to use it

- After the verdicts are set with `playbooks/review-search-terms.md`, to write the `negatives` list.
- "Clean up our negatives", "are our negatives blocking good traffic", "why is this keyword not getting impressions".
- Read `references/negative-keyword-matching.md` before explaining any match type to the person.

## What to read in the output

NEGATIVE KEYWORD TEST:
- "Tested against N Keep and Watch searches and M of the account's own keywords". Without the second half, the account's own keywords were not protected.
- "Passed", "Rejected", and the "NOTE:" lines: a search that cannot be Exclude, a campaign name not in the report, a negative that "stops no Exclude search in this report".
- **REJECTED**: "would block the Keep (or Watch) search ... (cost, conversions)" and "would block your own keyword ... in ...".
- **EXCLUDE SEARCHES NO PASSING NEGATIVE COVERS YET**, or "Every Exclude search is covered".

The summary: each passing negative with "Searches it stops" and "Cost it stops", and "Rejected by the test".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A word from the words list that no protected search contains, wrong for the whole business | A safe, wide negative | Phrase match at account level. For one word, phrase and broad block the same searches | Official (references/negative-keyword-matching.md) |
| A word wrong for one service only | Right elsewhere in the account | Campaign level, on that campaign | Official (references/negative-keyword-matching.md: levels) |
| A search that should go to a different ad group | Steering, not waste | Ad group level, and only for that | Practitioner rule |
| REJECTED: "would block the Keep search ..." | The word appears in a search that pays ("free" in "free estimate plumber") | Narrow it: a longer phrase that only the Exclude searches contain, or an exact negative for one search. Leave the rejected one in the file so the report shows what the test caught | Official (references/negative-keyword-matching.md) for how phrase and exact match; the rest is Practitioner rule |
| REJECTED: "would block your own keyword ..." | It conflicts with a keyword the account bids on | Narrow it, or move it to a campaign where that keyword is not | Practitioner rule |
| An uncovered Exclude search | No passing negative stops it | Add the narrowest one, often exact. Or leave it uncovered and say why | Practitioner rule |
| NOTE: "stops no Exclude search in this report" | A guess, not evidence | It is left out of the files. Tell the person if they want it anyway | Practitioner rule |
| A plural or singular form not in the report | Negatives do not match close variants | Tell the person "jobs" will not stop "job". Forms not in the report stop nothing here, so they are left out; the person adds them by hand | Official (references/negative-keyword-matching.md) |
| Misspelled brand or competitor searches | Negatives may not catch them | Point to brand exclusions; Google's pages disagree on misspellings, so name the disagreement if asked | Official (references/negative-keyword-matching.md, references/keywords.md) |
| A brand search in Performance Max | Negatives are restrictive there | Google recommends brand exclusions for brand protection | Official (references/keywords.md) |
| A negative for an AI Max search, AI Max on for less than 2 weeks | Too early | Hold it | Official (references/search-campaign-setup.md) |

## Cleaning up the negatives already in the account

The same test checks existing negatives for conflicts:

1. Ask for the negatives as the account holds them: account level lists, shared lists and which campaigns each is applied to, campaign negatives and ad group negatives. A list only works on the campaigns it is applied to. Official (references/negative-keyword-matching.md).
2. Run the measure step into a new work folder, on a 90 day report, with the keywords report.
3. List the existing negatives under `negatives` with their match type, level and campaign, and run the test.
4. Every REJECTED line is a conflict: an existing negative that blocks a search that converted or one of the account's own keywords. Recommend removing or narrowing it.
5. Do not run the write step for a cleanup. It would write those negatives out as new ones.

A negative already in the account stops its searches before they reach the report, so the test sees only the account's keywords and searches from before it was added. Practitioner rule. Say so.

Generic negative lists are the usual cause. Words like "how to", "guide", "template" or "free" are waste for one business and buyers for another. Judge each against the offer, not the list it came from. Practitioner rule.

## How big a change

- **Narrowest first.** Use the narrowest negative that stops the searches you mean to stop. Practitioner rule (references/negative-keyword-matching.md).
- **Widen slowly.** A negative safe in this report can block a good search that did not happen in this date range. Practitioner rule (references/negative-keyword-matching.md).
- **How many:** no source gives a number. Each passing negative prints the searches and cost it stops; drop those that stop little and carry risk. Judgment.

## Failure modes

- **One word at account level blocking a paying search.** "free" is the classic. Narrow it; never force it.
- **Negative broad read as broad match.** A negative broad keyword is far narrower. Official (references/negative-keyword-matching.md).
- **A wrong campaign name.** The test refuses it. Copy names exactly from the report.
- **A list never applied.** The account level list must be applied to every campaign it is meant for.

## Worked example

Northside Plumbing, sample run.

- 13 negatives proposed, 11 passed, 2 rejected. The passing negatives stop 2,634.70, every Exclude search.
- Both rejected negatives were "free" (phrase), on the two campaigns. They would block the Keep search "free estimate plumber" (cost 402.30, 7.00 conversions) and the account's own keyword "plumber free estimate", and the Keep search "free water heater estimate" (129.60, 2.00 conversions).
- Narrowed: "program" on Plumbing | Water Heaters stops "free water heater program" (159.30), and "course" at account level stops "free plumbing course" (98.60).
- "jobs" at account level stops 3 searches for 791.10. It will not stop "job"; the person adds that form by hand if wanted.
- Files: 4 campaign negatives for Google Ads Editor, 7 account level negatives for a negative keyword list.

## What to tell the client

"These 11 negative keywords stop 2,634.70 of spend on searches that will never book a job, and none of them blocks a search that brought you a lead. I did not add "free" on its own, because people searching for a free estimate are some of your best customers. Import the campaign file in Google Ads Editor, and paste the account list into a negative keyword list applied to every campaign."
