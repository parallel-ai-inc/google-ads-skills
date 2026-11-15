# Playbook: Naming and labels for campaigns and ad groups

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: judge whether campaign and ad group names follow one system, propose a system where they do not, and say what labels should carry instead. You read the **NAMING** section that `scripts/audit.py` prints from the names in the exports it already reads. It counts every pattern, so never count names yourself.

## When to use it

- Every full audit, briefly: one line in the answer unless the names get in the way.
- When the person asks for a naming convention, a tidy up, or why reports are hard to read.
- When several people or agencies have built in the same account.

Names do not decide serving, bidding or Ad Rank. This is housekeeping and reporting, so it never goes ahead of a measurement, serving or waste fix. In the fix plan it sits with structure, at stage 4 of `references/fix-order.md`.

## What to read in the output

- **Campaigns** and **Ad groups:** how many names, from which report, and every **Pattern** with its count. A pattern is the number of parts and the separator, such as `2 parts split by "|"`.
- **Most common pattern,** with its count of all names. If it says another pattern has as many names, there is no system yet.
- **Off that pattern:** each name that does not follow it, with its own pattern, and "not serving" when the campaign or ad group is paused or removed.
- **Part 1 holds ... different values:** for the most common pattern, what each position holds and how often. This is where a mixed system shows: one position holding services in some names and campaign types in others.
- **Names that differ only in capitals or spaces.**

Labels are not in the exports the audit reads. Check them by eye: in Google Ads, the Labels column in the campaign and ad group tables.

## A naming system to propose

Practitioner rule, unless labelled:

1. **One separator, one order.** For example `Service | Campaign type | Location`, or whatever the account already uses most. Keep the most common pattern unless it is unreadable. Fewer renames, less disruption.
2. **Each position holds one kind of thing.** A service or product line, then the campaign type, then the place or audience. A position that holds "Search" in one name and "Emergency" in another is not a system.
3. **Name only the splits that exist.** A campaign is split when the budget, the places, the conversion goal or the message must differ (Official, references/account-structure.md: split only when the split changes budget ownership, geo or language scope, conversion semantics, creative strategy or governance). The name should say which. A part that is the same in every campaign adds nothing.
4. **Brand keeps the system.** `Brand | Search` reads better in a report than `Brand`, and sorts beside the rest.
5. **Status and dates go in labels or in the status, not the name.** "Old", "Test" or "Paused" in a name outlives the state it describes.
6. **Ad groups are named for the theme the searcher has.** Plain words that match the landing page, such as `Burst Pipes`. No campaign name repeated inside the ad group name.
7. **Labels carry what changes.** Owner, test, season, client approval, launch date. Google allows 50 labels per entity (Official, references/ad-specs-limits.md). Labels are governance tools, not a substitute for clear ownership (Practitioner rule, references/account-structure.md).

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Most common pattern covers every name | There is a system. | Say so in one line. Check the part values for mixed meanings. | Practitioner rule |
| Off that pattern lists only names marked "not serving" | Old names in paused campaigns. | Leave them, or rename only if they are reported on. | Practitioner rule |
| Off that pattern lists a serving brand campaign | A common, deliberate exception. | Suggest the system's form, such as `Brand | Search`. Low priority. | Practitioner rule |
| Off that pattern lists serving non brand campaigns | Two systems, often from two builders. | Propose the most common pattern for all, and list each rename. | Practitioner rule |
| "No single most common one" | No system yet. | Propose one, using the order in rule 1. | Practitioner rule |
| A part mixes kinds of values | The position means different things in different names. | Name the values that do not belong, and where they should go. | Practitioner rule |
| Names differ only in capitals or spaces | Two items look like one in reports and filters. | Rename one, or check whether one is a stray copy. | Practitioner rule |
| A name holds a status or a date | It will go stale. | Move it to a label. | Practitioner rule |

## How big a change

No source gives a number. Rename in one batch, not over weeks, so reports have one cut-over date. Before renaming, check what is keyed to the old name: shared budgets, portfolio strategies and labels attached (Official, references/search-campaign-setup.md, Normal Operations), and outside the account, any Google Ads Editor files, scripts, saved filters and client reports that match by name (Practitioner rule). Renaming changes nothing about serving.

## Failure modes

- **Counting names by eye.** Use the printed counts.
- **Renaming paused campaigns that nobody reports on.** Effort with no reader.
- **A system that needs a legend.** Codes like `PLB_S_EM` save characters and cost every reader time.
- **Putting the name ahead of a real fix.** Naming is stage 4 at best.
- **Breaking a report.** A dashboard or script filtered on "Emergency" stops matching after a rename. Ask who reads the reports.

## Worked example

Northside Plumbing. Campaigns: 5 names. Most common pattern: 2 parts split by "|", 4 of 5. Off that pattern: Brand, 1 part. Part 1 holds 2 values, Drain Cleaning and Plumbing, both services. Part 2 holds 4 values: Emergency, Old, Search, Water Heaters. Two are services, one is a campaign type and one is a status word. So the system is half there. Propose `Service | Theme` for serving campaigns: `Plumbing | Emergency`, `Plumbing | Water Heaters`, `Drain Cleaning | Drains and Jetting` after its two ad groups, and `Brand | Search` for brand. Every campaign is Search, so the type adds nothing as a part of its own. "Old" belongs in a label on the paused `Drain Cleaning | Old`, which can otherwise stay. Ad groups: 8 names, one part each, no clash. Low priority: stage 4, after the conversion fix.

## What to tell the client

"Your campaign names mostly follow one pattern. Two small renames make every report sort and read the same way. Nothing about how the ads run changes."
