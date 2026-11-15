# Playbook: Keywords and Quality Score

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Which keywords earn their spend, which waste it, which cost more than they should, and which Quality Score component is holding the weak ones back. It reads the TOP AND BOTTOM KEYWORDS and QUALITY SCORE REVIEW sections that `scripts/review.py` prints from the keyword report.

## When to use it

- "Which keywords work", "what should I pause", "why is my Quality Score low".
- The searches behind a keyword, and the negatives that stop them, belong to the search terms skill in this pack. A keyword verdict tells you where to look; the search terms report tells you what to exclude.
- A landing page problem the Quality Score points to is settled with `ads-and-landing-pages.md` and the ACROSS REPORTS lines.

## What to read in the output

Keywords:
- "Baseline, every enabled non brand keyword" and "Enough to judge". Brand keywords sit on their own line.
- **Wasted**, **Less efficient** and "No conversions yet, under the line": three kinds of money, never added.
- "Spend concentration": how many keywords make up 80% of judged cost.
- The tables "Keyword winners", "Keywords with cost and no conversions", "Keywords that cost more per conversion than the baseline", "Worth watching" and "By match type", each row with Verdict, "Compared with" and "Cost / conv. vs it".

Quality Score:
- Per component (Exp. CTR, Ad relevance, Landing page exp.): the share of non brand cost rated Below average, its base, and those keywords' results against the rest.
- "Share of cost rated Below average, by scope", and "Non brand keywords with a component rated Below average, by cost" with each keyword's Verdict.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Verdict "No conversions", and the keyword is off offer (jobs, DIY, a product not sold) | Spend that will not convert | Pause the keyword, and add the matching negative through the search terms skill | Practitioner rule |
| Verdict "No conversions", and the keyword is a core service | Something between click and conversion is broken, or the searches behind it are wrong | Do not pause on sight. Check its search terms, its landing page and tracking first | Practitioner rule |
| "Worse, conversion rate" on a broad match keyword | The keyword matches searches that do not buy | Review its search terms. Tighten to phrase or exact if the converting searches are narrow | Practitioner rule |
| "Worse, cost per click" | The keyword pays more per click for the same conversion rate | Manual CPC: lower its bid. Smart Bidding: the strategy sets the bid; look at its target or the campaign's structure instead | Practitioner rule |
| "Better" keywords | The bets that pay | Protect them: they should not be limited by budget or rank. The export cannot show impression share, so check Search lost IS (budget) and (rank) in Google Ads | Practitioner rule |
| "Too little data" with cost and no conversions | Not yet spent enough to judge | Leave it. Say "too early to call", never "waste" | Practitioner rule |
| "Not enough data to judge" (Worth watching) | A wide gap the volume cannot prove | Name it with its gap. No action until a longer export proves it | Practitioner rule |
| A match type row judged Worse | The gap is in how keywords match, not one keyword | Look at the keywords of that match type in the Worse and No conversions tables first | Practitioner rule |
| "8 keywords make up 80%" and similar | Where the money sits | Spend the review on those keywords. A fix to a small keyword moves little | Practitioner rule |
| A component Below average on a large share of cost | A relevance problem on keywords that matter | Exp. CTR: the ad does not answer the search. Ad relevance: the ad group mixes themes; split it or rewrite the ads. Landing page exp.: fix the page | Official (references/quality-score.md) for the three components; the fixes are Practitioner rules from the same file |
| A component Below average on a keyword judged In line or Better | A diagnostic flag on a keyword that already pays | Low priority. The business result outranks the score | Official (references/quality-score.md: a diagnostic, not an auction input) |
| "1 enabled keyword shows no score" | Google has not rated it, usually for too little exact match traffic | Ignore it in the Quality Score story | Practitioner rule (references/quality-score.md: the score comes from exact match searches) |
| Brand keywords with high scores | Expected for brand searches | Keep them out of any Quality Score story | Practitioner rule (references/quality-score.md) |

## How big a change

- **Quality Score moves slowly.** It reflects exact match searches over the last 90 days, so a fix will not show next week. Official (references/quality-score.md). Re check after enough auctions; Practitioner rule from the same file.
- **Never target an average Quality Score.** Official (references/quality-score.md).
- **Bid changes.** No reference here gives a step size for a keyword bid. It is a judgment. The evidence that bounds it is the row's "Cost / conv. vs it" and its Less efficient amount. Say it is a judgment when you give a number.
- **One or two actions per week**, the ones with the clearest evidence. Practitioner rule (references/daily-optimization.md).

## Failure modes

- **Pausing a core keyword because it spent without converting.** If it is the service sold, check page, searches and tracking first.
- **Treating "Not enough data to judge" as proven.** Read the Verdict, not the gap.
- **Averaging Quality Score.** Use the cost shares the review prints.
- **Brand inside the baseline.** Without brand terms, every other keyword looks Worse. If the line "Brand keywords: cost ..." is missing, ask for brand terms.
- **Interactions counted as clicks without saying so.** The review prints it; pass it on.

## Worked example

Northside Plumbing, keyword report 2026-10-14 to 2026-11-12. Baseline 96.67 per conversion; enough to judge at 290.00.

- "plumbing jobs" spent 640.00 with no conversions (Wasted), Quality Score 3. It is off offer: pause it and add "jobs" as a negative through the search terms skill.
- "tankless water heater" (broad) costs 255.00 per conversion, Worse on conversion rate, 633.34 less efficient, Quality Score 3 with Exp. CTR and Landing page exp. Below average. Review its search terms and tighten the match type, and fix its page.
- By match type, Broad is Worse at 239.17 and Exact is Better at 60.70.
- Landing page exp. is Below average on 29.3% of non brand cost, and 100.0% of Plumbing | Water Heaters cost. That is one page problem, not four keyword problems.
- "hydro jetting" (2 conversions, 240.00 each) is Worth watching. No action yet.

## What to tell the client

"Most of your keyword spend works. Exact match keywords bring leads at 60.70 each against 96.67 overall. One keyword, plumbing jobs, spent 640.00 on job seekers, and I recommend pausing it. Your water heater keywords are let down by their landing page, which Google rates below average, so the page is the next fix rather than the bids."
