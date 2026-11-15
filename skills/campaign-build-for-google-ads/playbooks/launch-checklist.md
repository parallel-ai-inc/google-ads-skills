# Playbook: Launch checklist, owners and the first 14 days

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: decide what still stops the launch, who owns each item, how each warning is settled, and what to watch in the first 14 days. You read the **LAUNCH BLOCKERS**, **WARNINGS** and **ASSUMPTIONS WRITTEN IN THE PLAN** that `scripts/check_plan.py` prints, and the `launch-checklist.md` that `scripts/write_build.py` writes.

## When to use it

Every build, once the plan passes. It is also the answer when the person asks "what is left before we go live" about a build from this skill. For an account that already runs, the account audit skill's readiness check fits better.

## What to read in the output

- **LAUNCH BLOCKERS:** each "Must be true before launch" item, its "Answer in the plan" (yes, no or unknown) and its Owner, then "No owner is named for: ...".
- **WARNINGS (N):** numbered, each with where it is.
- **ASSUMPTIONS WRITTEN IN THE PLAN.**
- In `launch-checklist.md`: the sections Stop launch, Import and review in Google Ads Editor, Launch day, First 14 days, and Warnings from the plan check. Each item has an Owner and a Status.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A blocker answered no or unknown | The launch waits. The files can still be written. | Name it, with its owner, in your reply. Write yes in the plan only when the person said so. | Practitioner rule |
| "No owner is named for" a role | Nobody will close that item. | Ask the person who owns it. Never fill in a name. | Practitioner rule |
| Conversion tracking blocker open, on a conversion bid strategy | The campaign has nothing to learn from. | Keep it a stop item. If it cannot be fixed before launch, move the plan to Maximize clicks and run the check again. | Practitioner rule (references/campaign-launch.md) |
| Ad text not approved | Claims, prices and offers are the business's to confirm. | Stop item. Send the Ad text sheet, and list any claim you could not source. | Practitioner rule |
| Landing pages not confirmed | A page that does not load or does not match wastes every click. | Stop item: each final URL on a phone and a computer, and the page offers what the ad offers. | Practitioner rule (references/campaign-launch.md) |
| A warning about a keyword already in the account | Two copies compete for the same searches. | Decide which campaign keeps it, and put "pause the other" on launch day. | Official (references/account-structure.md) |
| A warning about one ad in an ad group | Google's tip is at least 2. | Fine to launch. Note when a second, different message will follow. | Official (references/build-limits-and-editor-import.md) |
| A warning naming a customizer attribute | The ad cannot be reviewed without the attribute and a value. | Add "create the attribute with a value" to the Editor section, before posting. | Official (references/ad-customizers.md) |
| A warning naming a countdown end date | The ad stops showing after it. | Add the date to the first 14 days, or later, with an owner to change the headline. | Official (references/ad-customizers.md) |
| An assumption the person has not seen | A choice they did not make. | Read each one to them. Change the plan if they disagree. | Practitioner rule |
| The account runs other campaigns with the same keywords or tracking templates | Changes can reach live campaigns through shared negatives, lists or templates. | Check what is shared before posting. Tracking templates need the landing page URL kept intact. | Practitioner rule |

## How big a change

- **What it can spend:** up to 2 times the daily budget in one day, and at most 30.4 times in one month (Official, references/build-limits-and-editor-import.md). The checklist prints both for this build. Read them to the budget holder.
- **First 14 days:** watch serving eligibility, pacing, tracking health and search term quality before structural changes, and do not stack changes while the first signals form (Practitioner rule, references/campaign-launch.md).
- **AI Max:** if it is on, wait at least 2 weeks after enabling before changes such as adding negatives (Official, references/search-campaign-setup.md). Google also says it will not be effective while the campaign is limited by budget.
- **Order on launch day:** enable ads, keywords and ad groups, then the campaign last (Practitioner rule, references/build-limits-and-editor-import.md).
- No source gives a number for when to judge results. Bound it by the conversion delay the business knows and the volume the budget can buy.

## Failure modes

- **Calling a build launch ready.** Structure in a file is not an approved, tracked, truthful ad journey. The answer lists every open stop item.
- **Mixing stop items with nice to haves.** Stop items block. Warnings are decided. The first 14 days are watched.
- **Enabling the campaign first.** Half built parts serve.
- **Judging day three.** Late conversions and low volume look like failure. Check conversion delay before calling it.
- **Stacking changes in week one.** Nothing can be read afterwards.
- **Assuming the import matched.** Count the proposed changes in Editor against the checklist's numbers, and confirm every row reads Paused before posting.

## Worked example

Northside Plumbing, "Sewer Line | Search". LAUNCH BLOCKERS: conversion tracking yes (Lee), billing yes (Dana), budget yes (Dana), locations yes (Dana). Two remain: every final URL loads and matches, unknown, with no owner named for Landing pages; and the business approved the ad text, answered no (Dana). So the files are written, and the launch waits on both. WARNINGS (2): two ad groups have one ad, which is fine to launch; and "sewer line repair" (phrase) already runs in Drain Cleaning | Search > Sewer Repair, which needs a decision before launch day. Pacing for the first 14 days: up to 240.00 in a day, at most 3,648.00 in a month.

## What to tell the client

"The campaign is built and paused. Two things stand between us and launch: someone needs to open each landing page on a phone and a computer, and you need to approve the ad text. Who should own the landing pages? Once both are done, we enable it and watch it closely for two weeks before changing anything."
