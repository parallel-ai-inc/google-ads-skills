# Playbook: Who is taking share, and who is giving it away

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Whether a campaign lost impression share because a competitor took it or because the account gave it away, who the competitors are, and what to do. It reads the "In short", "Auction insights", "Share of voice", "Competitor landscape" and "Checks" sections of `competitive-and-market.md`.

## When to use it

Competitors, auction insights, impression share, share of voice, "why are we showing less". Seasonality and year on year: `playbooks/seasonality-and-year-on-year.md`.

## What to read in the output

- **In short:** the line for the campaign asked about, before the account line.
- **Campaign report for the same scope:** the bold reading and the line under it, which names competitors that "showed above you more often by a large move, or entered", or says the auction data does not show one.
- **The competitor table** with its changes, and the printed "large" line.
- **Share of voice:** Reading, "What the share lost stands for", and "Spend beside lost share" (Of budget, Avg. CPC).
- **Competitor landscape:** Periods seen and Pattern. **Checks:** the You row against the campaign report, and any "Does not add up" flag.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "mostly lost to budget", with no "Does not add up" flag | The account gave the share away | Fix it inside the account: budget, or a looser target. Quote impressions missed because of budget and cost / conv. More budget buys the next auctions, not the average ones | Practitioner rule |
| "mostly lost to budget", but cost / conv. is above the person's goal | More budget buys more of what already costs too much | Fix efficiency first, or agree the goal before adding budget | Practitioner rule |
| The "Does not add up" flag | Lost to budget rose while the budget and spend did not | Report the flag and its checks in order. Ask whether the budget changed before calling it a budget problem | Practitioner rule |
| "mostly lost to rank", and the line names a competitor | A competitor is likely taking share. It is a lead, not proof | Check the account's own changes first. Then answer through Ad Rank: bid, ad quality, assets, landing page | Official (references/auction-physics.md) |
| "mostly lost to rank", and "the auction data does not show a competitor taking this share" | The cause is most likely inside the account, or Ad Rank thresholds moved | Change history, ad quality, landing page, bids and targets, in that order | Practitioner rule |
| Avg. CPC rose while Search impr. share fell | More pressure per auction | Check competitiveness, thresholds, assets and landing page before treating bids as the only lever | Practitioner rule |
| A competitor's impression share rose by a large move, and the account's share held | They grew in auctions you share without taking yours | Note it and watch. No change yet | Practitioner rule |
| A reading of "unclear", "Too close to call", or a band such as "< 10%" | Google gives a band, not a number | Quote the band and the range exactly. Name no cause | Official (references/auction-insights-and-impression-share.md) |
| A competitor "not seen" in the latest period | Not in this report's auctions in that period | Never say they left the market | Practitioner rule |
| The account line points one way and the campaign line another | Other campaigns move the account line | Lead with the campaign asked about | Practitioner rule |
| A large gap between the You row and the campaign report in Checks | The files cover different campaigns or dates | Resolve it before quoting either | Practitioner rule |
| Landscape: "in every period" with the highest overlap rate | The structural competitor | Name them first in the landscape | Practitioner rule |
| Landscape: "first seen" a recent period | A new entrant | Short term until it persists. Watch its Position above rate | Practitioner rule |
| "google.com" as a domain | Advertisers using Google hosted domains, a Business Profile or a Google Site | Not Google competing | Official (references/auction-insights-and-impression-share.md) |
| The person wants to answer a competitor | Their ads can be seen, their bids cannot | Look at their ads in Google's Ads Transparency Center first. Respond with message, offer, landing page or budget priority, from the account's own evidence | Practitioner rule |

**What may never be said.** Auction insights shows overlap, position, outranking and impression share in the auctions the account entered. It has no statistic for spend, bids, budget, settings, Quality Score or strategy. Official (references/auction-insights-and-impression-share.md). Say "showed above you more often" or "appeared in more of your auctions". Never "raised their bids", "increased their budget", "is targeting your brand" or "is running a promotion".

## How big a change

- **What counts as large.** The script marks a move large at 3 times the typical move in that file and prints the line. It decides what to look at first, not what is shown. A small change in impression share does not always need action. Official (references/auction-insights-and-impression-share.md).
- **Budget steps.** No source gives a step. The evidence is the impressions missed because of budget, Of budget, and cost / conv. against the person's goal. The amount is the person's call; for a month by month plan use the budgets and forecasts skill.
- **Reading after a change.** Impression share updates within 1 to 2 days. Official (references/auction-insights-and-impression-share.md). Compare complete periods only; the script leaves partial ones out.

## Failure modes

- **Bids or budget claimed for a competitor.** Check every competitor sentence against the list above.
- **Rank loss blamed on a rival without checking the account.** Were the account's own changes asked about?
- **A budget problem called when the budget changed.** Check the "Does not add up" flag.
- **The account line used for one campaign.** Quote the campaign's own line.
- **A band read as zero or as a number.** Check every "< 10%".

## Worked example

Northside Plumbing, 2026-10 against 2026-09. Plumbing | Emergency: Search impr. share 49.0% to 44.0% (-5.0 pts), lost to rank +6.0 pts, "mostly lost to rank". rapidrooter.example showed above it more often (position above rate +7.4 pts, large), its impression share rose 13.6 pts, it was first seen in 2026-08, and the account outranked it less often (-3.9 pts). Avg. CPC went from 6.89 to 7.43. The call: a competitor is likely taking Emergency's share. Check Emergency's own changes since August, then look at their ads before answering through ad quality, assets, landing page and bids. Plumbing | Water Heaters: 62.0% to 55.9%, lost to budget +16.0 pts, Of budget 99%, about 2,992 impressions missed because of budget at 81.09 per conversion, and no competitor moved: the account gave this share away.

## What to tell the client

Your emergency campaign is losing ground to a newer competitor, rapidrooter, who started appearing in August and now shows above you more often. We cannot see what they spend, only how often they appear and rank, so the first step is to check our own recent changes and look at their ads. Your water heater campaign is a different story: it runs out of budget, and that is ours to fix.
