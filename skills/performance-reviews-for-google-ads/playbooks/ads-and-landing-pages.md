# Playbook: Ads and landing pages

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Which ads win inside their ad group, which pages lose the click after it lands, and whether a weak page or weak traffic is to blame. It reads the AD PERFORMANCE, LANDING PAGES and ACROSS REPORTS sections that `scripts/review.py` prints from the ads report and the landing page report.

## When to use it

- "Which ads work", "should I pause this ad", "which pages convert", "is the page the problem".
- Keyword level findings are in `keywords-and-quality-score.md`. Its Landing page exp. line and this playbook's page verdicts should be read together.
- Video ads and their view rate are in `placements-and-video.md`. Demand Gen ads follow the creative rules in `demand-gen-review.md`.

## What to read in the output

Ads:
- "Ads are compared only with the other enabled ads in the same ad group". An ad is "Judged on" conversions per impression when the volume allows, otherwise on CTR.
- Verdicts "Leads its siblings" and "Trails its siblings", with "Gap to siblings" and Less efficient.
- "Ad groups with two or more enabled ads" and "With only one, so nothing to compare".
- "Ad strength of the enabled ads" and the "Disapproved, left out of the comparison" line.

Landing pages:
- "Baseline, all pages judged", "Enough to judge", Wasted and Less efficient.
- "This file has no Campaign column, so brand traffic could not be set apart". When printed, brand clicks sit inside the baseline.
- "N addresses were grouped into M pages by leaving out what follows '?' or '#'".
- "Mobile speed score and mobile friendly click rate, as the file gives them".

ACROSS REPORTS: one line per page theme, saying whether the keywords on that theme agree with the page's verdict, and where their final URL points.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| An ad "Trails its siblings", judged on conversions per impression | Its message loses to another ad shown to the same searches | Write a new ad on the leading ad's angle, then pause the trailing one. Never leave an ad group with no enabled ad | Practitioner rule |
| An ad "Leads its siblings" | The angle that works in that ad group | Reuse its promise in the ad group's new ads and on its page | Practitioner rule |
| Judged on CTR, not conversions | Too few conversions to compare | Treat a CTR lead as an early read, not a business win | Practitioner rule |
| Ad group with only one enabled ad | Nothing to compare | Add a second ad if the ad group spends enough to matter | Practitioner rule |
| Ad strength Poor or Average | Asset coverage is thin | Add headlines and descriptions. Do not pause an ad for its Ad strength alone | Official (references/creative.md: a diagnostic for asset coverage, not an auction input) |
| A disapproved ad | It is not serving | Fix it first. The export cannot show the policy detail, so read it in Google Ads | Practitioner rule |
| A page "Worse", and ACROSS REPORTS says its keywords agree (Landing page exp. Below average) | A page problem | Fix the page: speed, the promise the ad made, the form or call button | Practitioner rule |
| A page "Worse" while the keywords on its theme are Worse too | The traffic, not the page | Fix the keywords and searches first, then judge the page again | Practitioner rule |
| A page "No conversions", and ACROSS REPORTS says the keywords convert and point to another final URL | The page's clicks come from other traffic | Find which campaigns send it traffic, and check its tracking, before pausing anything | Practitioner rule |
| The home page judged Better with a very low cost per conversion, and no Campaign column | Brand searches land there | Do not read it as a page win, and do not send non brand traffic there on this evidence | Practitioner rule |
| The lowest Mobile speed score in the file, or a mobile friendly click rate under 100% | A mobile experience gap on that page | Name it with the page's verdict. Fix it first if the page is also Worse | Practitioner rule |
| A page judged on a thin "?" variant | Addresses were grouped | Judge the grouped page; tracking parameters are not separate pages | Practitioner rule |

## How big a change

- **Ads.** No source here gives a fixed waiting period before replacing an ad. The script already requires the gap to beat chance before it says Leads or Trails. Replace one trailing ad per ad group at a time, so the next review can read the change. Practitioner rule.
- **Pages.** A page change touches every campaign that sends traffic to it. Change one page at a time and say which campaigns land there. Practitioner rule.
- **Quality Score lag.** A better page shows in Landing page exp. only over the following weeks, since the score reflects the last 90 days. Official (references/quality-score.md).

## Failure modes

- **Comparing ads across ad groups.** Different searches, different results. Compare siblings only.
- **Calling a page broken when its traffic is wrong.** Check ACROSS REPORTS before blaming the page.
- **Brand inflating the home page.** Check for the "no Campaign column" line.
- **Ad fatigue claimed from one export.** One date range cannot show decay over time. Compare two exports, or say it cannot be seen.
- **Ad and page claims that do not match the offer.** An ad that promises a price, a speed or a feature the business does not deliver converts badly and risks policy. Check the promise against what the business really sells. Practitioner rule.

## Worked example

Northside Plumbing, ads and landing page reports 2026-10-14 to 2026-11-12.

- In Plumbing | Emergency > Emergency, "24/7 Emergency Plumber | Here in 60 Minute..." leads its siblings (+267%), and "Emergency Plumbing Service | Fair Upfront ..." trails (-73%, 1,536.36 less efficient). Call: write a new ad on the 60 minute promise, then pause the trailing ad.
- Hydro Jetting Specialists in Drain Cleaning | Search > Hydro Jetting is disapproved (cost 357.00). Fix it first.
- The water heaters page is Worse: 165.04 per conversion against 81.51, 2,422.37 less efficient, Mobile speed score 3, mobile friendly click rate 94.0%. ACROSS REPORTS agrees: Landing page exp. is Below average on 4 water heater keywords. Fix the page.
- The hydro jetting page spent 520.00 with no conversions, but its keywords converted and point to the drain cleaning page. Its traffic comes from elsewhere: find the source and check tracking before pausing anything.

## What to tell the client

"Your emergency ad that promises a plumber within 60 minutes is clearly the stronger one, so I would write a second ad on that promise and retire the weaker one. The water heater page is where leads are being lost: each lead from it costs 165.04, against 81.51 across your pages, and it scores 3 for speed on phones. Fixing that page is the biggest single improvement available this month."
