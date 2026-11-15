# Playbook: Review search terms and find the waste

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The judgment behind every verdict: which searches to keep, watch or exclude, which deserve their own keyword, and how to tell waste from a search that is only early. It reads what `scripts/measure.py` prints and the theme and campaign totals that `scripts/write_outputs.py` writes.

## When to use it

- A full review of a search terms report, 30 or 90 days.
- A quick check of this week's waste: the same steps on a 7 or 14 day export. Few searches reach the line, so most stay Watch. Call it an early read and add no wide negative from it. Practitioner rule.
- Writing, testing and cleaning up negatives: `playbooks/negative-keywords.md`. Pausing keywords: the performance reviews skill.

## What to read in the output

- LOAD REPORT: "Difference from rows" must be 0.00 before you judge anything. "Not listed by Google (low volume searches)" is cost outside the review; every share is of listed cost. "Spent enough to judge: ... That is ..." gives the line and its source: your target, the non brand cost per conversion, the account's own, or the top tenth by cost when nothing converted. Then "AI Max share of cost" and the counts by class.
- **EXCLUDE CANDIDATES TO JUDGE (n of m, by cost)**: no conversions, cost at or above the line.
- **SEARCHES TO PROTECT**: Keep and Watch, with "Cost / conv." and "Cost / conv. against the line".
- **SEARCHES THAT NAME A COMPETITOR**, when `--competitors` was given, with their total.
- **WORDS AND PHRASES IN TWO OR MORE SEARCHES**: no conversions anywhere, cost at least half the line.
- After the write step: "Where the wasted spend goes" by theme, and "By campaign".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| An Exclude candidate asking for something the business does not offer (a job, training, parts, a manual, do it yourself, a free program) | It will never become a sale | Exclude, with a reason in the person's words and a theme | Practitioner rule |
| An Exclude candidate that is the business's own service, or matches one of its keywords | Relevant search, no sale yet | Watch, never Exclude. Spend without a conversion is not proof. Check its ad, page and tracking | Practitioner rule |
| Watch: "Too few clicks to judge" (under 3 clicks, the script's default) | Not enough to say anything | Leave it. Use a 90 day export if it matters | Practitioner rule |
| Watch: "spent less than a conversion costs here" | Relevant, under the line | Leave it. Move it to Exclude only when its reason is as clear as the other Exclude rows | Practitioner rule |
| Keep with a negative "Cost / conv. against the line" and several conversions, matched by a broad, phrase or AI Max keyword | A proven search the account reaches only by expansion | Say it deserves its own keyword (exact or phrase) when that gives it its own ad, bid or page | Practitioner rule |
| Keep with a positive "Cost / conv. against the line" | It converts, at more than the line | Never a negative; the test refuses it. Name it under "calls to check" as a bid, match or page question. On one conversion, say it proves little | Practitioner rule |
| A competitor search the person does not want (names only from the person) | Unwanted by policy | Exclude, theme "Competitors". If it converted it stays Keep: show the person. If they want them, judge it like any search | Practitioner rule |
| A search naming a maker the business serves (a water heater brand) | Its owner may be a customer | Negate the off offer part ("manual", "parts"), not the name | Practitioner rule |
| How to, guide or template searches | Depends on the offer | Usually Exclude for a service done for the customer. For a business selling the tool or know how, they can be buyers | Practitioner rule |
| A search matched through AI Max | Same judgment | If AI Max was turned on less than 2 weeks before the report ends, hold the negatives for those searches | Official (references/search-campaign-setup.md) |
| The line came from "the top tenth of searches by cost, because this report has no conversions" | No conversions recorded at all | Check conversion tracking first. Exclude only searches that are plainly off offer | Practitioner rule |
Brand searches are always Keep. The scripts enforce it. A word in the words list goes to `negative-keywords.md`.

## How big a change

- **The line, the 3 click minimum and the words list threshold** come from the script and are printed. The line decides what is looked at first, never the verdict.
- **Window:** 30 days by default; 90 days when most searches sit on Watch for too few clicks. Practitioner rule.
- **AI Max:** at least 2 weeks after turning it on before changes such as adding negatives. Official (references/search-campaign-setup.md).
- **How much to exclude in one pass:** no source gives a number. The bound is the Exclude share of listed cost and the test's result. Say it is a judgment.

## Failure modes

- **Excluding a core search because it spent without converting.** If it shares words with a Keep search or a keyword, Watch.
- **Brand in the line.** Cheap brand conversions lower it. If LOAD REPORT says "this account's own" and brand searches exist, run again with `--brand`.
- **A short window read as a full review.** If Watch dominates the counts, say it is early.
- **Shares without a base.** Say "of listed cost", and give the unlisted cost.
- **Conversions that are not sales.** If the account counts soft actions, a "converting" search may not pay. Ask what Conversions counts.

## Worked example

Northside Plumbing, search terms report October 14 to November 12, 2026.

- LOAD REPORT: 34 searches, 10,480.80 cost, difference 0.00, and 612.40 unlisted. The line is 90.35, the non brand cost per conversion.
- "plumbing jobs near me" spent 468.60 with no conversions: Exclude, theme "Job seekers". "jobs" is in 3 searches for 791.10.
- "emergency plumber" spent 82.80 on 9 clicks with no conversions, under the line. It is the core service: Watch.
- "water heater replacement cost": Keep, 4 conversions at 127.10, +41% against the line. A call to check, not a negative.
- With `--competitors "home depot, rheem"`: 2 searches, 328.50, no conversions. "rheem water heater manual" is Exclude for "manual", not for "rheem".
- Result: 14 searches to exclude, 2,634.70, 25.1% of the listed cost; Job seekers is the largest theme at 930.30.

## What to tell the client

"About a quarter of your search spend in the last 30 days, 2,634.70 of 10,480.80, went to searches that cannot become a job: people looking for plumbing work, training, parts or how to guides. I have listed negative keywords that stop them, and checked each one against every search that brought you a lead. A few searches fit your services but have not converted yet; we leave them running and look again next month."
