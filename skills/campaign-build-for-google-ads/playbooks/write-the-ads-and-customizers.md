# Playbook: Write the responsive search ads, with customizers where they earn a place

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: write each ad group's responsive search ads, decide whether a keyword, location, countdown or ad customizer code belongs in them, and answer every refusal and warning on ad text. You write the `ads` of `plan.json`. `scripts/check_plan.py` counts every character, including codes in braces, so never count yourself.

## When to use it

Every build, after the structure in `playbooks/plan-the-search-campaign.md` is settled. The customizer syntax and limits are in `references/ad-customizers.md`. Open it before writing any code in braces.

## What to read in the output

- **AD TEXT:** each headline and description with Characters and Limit, the Final URL, the Paths, and "Headlines with a keyword of the ad group: N of M". A code counts as its default text, a countdown as 8 characters.
- **CHECKS** on ad text, above all "Every code in braces is one Google reads in a responsive search ad, with default text, inside the limits", and the **WARNINGS** with where each one is.

## The decisions

| What you see | What it means | What to do | Label |
|---|---|---|---|
| Writing headlines | Google shows them in any order, up to 15, each 30 characters. | 8 to 15 headlines. Each true, specific and readable beside any other. Never pad to 15. | Official (references/build-limits-and-editor-import.md) for the limits. Practitioner rule for 8 to 15. |
| A claim the person did not state and the landing page does not show | A licence, price, guarantee, free offer, hours or response time that may be false. | Leave it out, or ask. | Practitioner rule |
| "Headlines with a keyword of the ad group: 0" | Google's tip is at least one keyword in the headlines. | Add a headline with the keyword's words, or a keyword insertion code. | Official (references/build-limits-and-editor-import.md) |
| A headline or description refused for length | Over 30 or 90 characters as counted. | Shorten the words. If the line holds a code, shorten its default text. | Official (references/build-limits-and-editor-import.md) |
| An editorial warning | Phone number, repeated punctuation, emoji or capitals for effect. | Reword. Put the number in a call asset. Keep real abbreviations. | Official (references/build-limits-and-editor-import.md) |
| One ad in an ad group | Google's tip is at least 2 rated Good or Excellent, at most 3 enabled. | One is enough to launch. Add a second only with a different message to test, not the same descriptions reworded. | Official (references/build-limits-and-editor-import.md) |
| Text that must always show | Pinning is the only way, and Google does not recommend it for most advertisers. | This skill writes no pins. Pin in Editor only for legal text. | Official (references/build-limits-and-editor-import.md) |
| The ad group's keywords all read well in one sentence | Keyword insertion fits. | `{KeyWord:Default text}`. The capitals of the code set the keyword's capitals. Default text is a real phrase. | Official (references/ad-customizers.md) for syntax. Practitioner rule for when. |
| One keyword in the ad group reads badly in the sentence | It will show as written. | No keyword insertion in that ad group. | Practitioner rule |
| The campaign serves several cities and the ad names a place | Location insertion fits. | `{LOCATION(City):Default text}`, at a level that fits the campaign's locations. One per headline, two per description. | Official (references/ad-customizers.md) |
| The business has a real end date, such as a sale | A countdown fits. | `{COUNTDOWN(yyyy-MM-dd HH:mm:ss,daysBefore)}`. At least 3 headlines without one. Confirm the date with the business. | Official (references/ad-customizers.md) |
| A value that changes by campaign or ad group, such as a price | An ad customizer fits. | `{CUSTOMIZER.Name:Default text}`. The person creates the attribute and a value in Google Ads before posting. | Official (references/ad-customizers.md) |
| "Every code in braces ..." refused | Google would not read the code, or it breaks a rule. | Fix it as the message says: capitals, level, date, missing default text, an old text ad form, an IF function, a code in the Final URL. | Official (references/ad-customizers.md) |
| A warning names a customizer attribute | The import does not create it. Without a value the ad cannot be reviewed. | Tell the person to create it in Tools, Business data, Ad customizer attributes, with a value, before posting. Add it to the launch checklist. | Official (references/ad-customizers.md) |
| A warning names a countdown's end date | The ad stops showing after it. | Agree who changes the headline on that date. | Official (references/ad-customizers.md) |
| A warning names a code in a path | Google's Help and API guide disagree. | Keep the path plain unless the person wants it, then read it in Editor. | Official (references/ad-customizers.md) |

## How big a change

- Headlines 3 to 15, descriptions 2 to 4, paths 15 characters each, a double width character counts as 2 (Official, references/build-limits-and-editor-import.md).
- A code counts as its default text, and a countdown as 8 characters. Up to 40 customizer attributes per account (Official, references/ad-customizers.md).
- Ad strength is feedback on variety, not a ranking input. More assets is not more effect on its own (Official, references/creative.md).
- How many ads to test at once is a judgment: Google allows 3 enabled per ad group, and each needs its own message.

## Failure modes

- **Claims nobody made.** The first trial run wrote "Licensed" and "Free Quote" with no source. Every claim needs the person's word or the landing page.
- **Padding.** Fifteen weak headlines dilute the ad. Stop at the true ones.
- **A default text that does not read alone.** `{KeyWord:Here}` shows "Here" whenever no keyword fits.
- **A code nobody can fill.** A customizer attribute with no value stops the ad from being reviewed.
- **Keyword insertion with loose negatives.** Google notes that search terms not covered by negatives can appear in the ad text. Review negatives in ad groups that use it.
- **A countdown that outlives its date.** The ad stops showing. Name who changes it.
- **The same message in two ads.** It tests nothing.

## Worked example

Northside Plumbing, "Sewer Line Repair" ad 1: 12 headlines, 4 descriptions, 4 headlines carry a keyword. In the first draft, the replacement ad's "Trenchless Sewer Line Replacement" was refused at 33 characters against 30, and its Path 1 "sewer-replacement" at 17 against 15. With a location code, "Sewer Repair in {LOCATION(City):Denver}" counts 22, because "Denver" stands in for the code. "{KeyWord:Sewer Line Repair}" counts 17. The campaign serves Denver and Aurora at city level, so the location code fits. No countdown, because the brief names no end date. No customizer, because no price varies by ad group.

## What to tell the client

"Each ad group has its own ad, written only from what you told us and what your pages say. Please check every claim is true before we launch. Where an ad names your city, it shows the searcher's city from your service area, and Denver when it cannot tell."
