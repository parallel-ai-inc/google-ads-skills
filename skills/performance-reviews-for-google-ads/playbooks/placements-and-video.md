# Playbook: Placements, brand suitability and YouTube ads

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Where the Display and video ads showed, which places suit the brand, and which videos hold viewers. It reads the PLACEMENTS AND BRAND SUITABILITY and YOUTUBE ADS sections that `scripts/review.py` prints, and the video itself when you can watch it.

## When to use it

- "Where are my display ads showing", "is this placement safe for the brand", "which video works", "where do viewers drop off".
- A Demand Gen campaign also serves on YouTube and the Display Network. Read its placements and videos here, and its bidding, budget and creative refresh in `demand-gen-review.md`.

## What to read in the output

Placements:
- "Baseline, all placements judged" and "Enough to judge". Display conversion rates are low, so the line is often high.
- Wasted, and "No conversions yet, under the line (not called waste)".
- "By placement type": Website, Mobile application, YouTube channel, each with its share of cost and of impressions and its cost per conversion.
- The placements table with Verdict, and "Worth watching".
- "Where the ads were seen most, by impressions, for the brand suitability check". The names are data; the file cannot show what a page or video was about beyond its name.

YouTube ads:
- "Baseline, every video judged: view rate ..., avg. CPV ...".
- Per video: View rate, "vs baseline", "View rate verdict" (Higher or Lower view rate), Avg. CPV, conversions and their Verdict, and "Largest drop" between quarters.
- The line "If a campaign's goal is awareness or views, spend with no conversions is not waste for it", and the note that on large counts a small view rate gap can pass the test.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A placement "No conversions" whose name does not suit the brand | Wasted and unsuitable | Exclude it. An exclusion removes it whatever the bid strategy | Practitioner rule (references/bid-adjustments.md) |
| A placement name that does not suit the brand, with "Too little data" | A suitability problem, not a performance verdict | Exclude it on suitability alone. Say that is the reason | Practitioner rule (references/display-video.md: suitability matters more off Search) |
| Mobile application type with a large share of impressions and few conversions | App inventory taking the reach | Review the app placements by name. Check the account's content suitability settings in Google Ads | Practitioner rule |
| "Worth watching" with a low cost per conversion | Promising, not proven | Leave it running. Do not move budget on it yet | Practitioner rule |
| Many tiny placements with "Too little data" | Normal long tail | Ignore them unless a name fails the suitability check | Practitioner rule |
| A video with "Lower view rate" | Viewers skip it more than the account's other videos | Look at the opening seconds and the "Largest drop". If you can watch the file, do the scene check below | Practitioner rule |
| A video with "Higher view rate" and conversions In line | It holds attention and converts like the rest | Keep it. Use its opening as the model | Practitioner rule |
| A video with no conversions under the line | Too early to call on conversions | Judge it on view rate. On conversions, say "too early to call" | Practitioner rule |
| Awareness or views campaign with no conversions | Not its goal | Never call that spend waste | Practitioner rule (printed by the review) |
| Every video's largest drop at the same quarter | A pattern in how the videos are built | Name the quarter. The fix is in the edit, not the bids | Practitioner rule |
| A Display campaign in the file | Display is moving into Demand Gen | A migration carries settings and up to 42 days of history and cannot be undone; do not migrate during a lift study | Official (references/display-video.md) |

## The scene check

Only when you can watch the video file. A file name, a title or the ad's copy is not the video. Practitioner rules:

- List the scenes in order with their timestamps.
- Mark the moment the hook, the offer, the proof, any required disclosure and the call to action appear.
- Compare each moment with the ad's headline, description and call to action, and say where they match or miss.
- Check the format: in stream, bumper, in feed, Shorts or Demand Gen video, and its length.
- Separate a policy risk from a quality issue.
- Cite the timestamp for every finding, and never invent one. Infer no performance for a video that has never run.

## How big a change

- **View rate gaps.** The review calls a gap only when chance would give it less than 1 time in 10, and warns that a small gap can pass on large counts. Read "vs baseline" before acting; a small gap is not worth a new edit. Judgment.
- **Exclusions.** No source gives a number. Exclude what is wasted or unsuitable by name; leave the long tail.
- **Lift claims.** Never promise a fixed recall or intent lift from a creative change. Official (references/display-video.md, What not to present as fact).

## Failure modes

- **Excluding the long tail on performance.** "Too little data" proves nothing either way.
- **Judging a view campaign on conversions.** Check its goal first.
- **A scene by scene review without the video.** Without the file, say the check needs it.
- **Treating Demand Gen as plain Display or plain YouTube.** It has its own rules. Official (references/display-video.md).
- **Calling a placement safe from its name.** The name is all the file shows. Say so.

## Worked example

Northside Plumbing, placement and video reports 2026-10-14 to 2026-11-12.

- Bubble Shooter Classic, a mobile app, spent 380.00 with no conversions on 48,000 impressions: wasted and unsuitable for a plumbing brand. Exclude it.
- Late Night Crime Stories spent 70.00, too little data, and does not suit the brand by name. Exclude it on suitability.
- Mobile application takes 58.7% of impressions and 44.7% of cost, for 1 conversion at 540.00. Review the app placements.
- Home Repair Weekly brought 9 conversions on 300.00 but is Worth watching. Leave it running.
- Meet Our Plumbers (60s) has a Lower view rate, 15.0% against 27.0% (-44%), and loses 39.0 points between 25% and 50%. Its 420.00 with no conversions is under the 574.20 line, so too early to call on conversions. All three videos lose the most viewers between 25% and 50%.

## What to tell the client

"Some of your display budget went to a mobile game, which brought no leads and does not suit the brand, so I am excluding it along with one other site. Your 15 and 30 second videos hold viewers well. The 60 second one loses most of its audience in the second quarter, so a tighter edit with the offer earlier is the next test."
