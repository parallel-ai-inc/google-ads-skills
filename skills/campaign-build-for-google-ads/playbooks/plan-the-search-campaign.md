# Playbook: Plan a new Search campaign

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: turn the brief, and what the account already has, into campaigns, ad groups, keywords with match types, a bid strategy, a budget and three levels of negatives. You write `plan.json` from what `scripts/start_build.py` prints, then answer what `scripts/check_plan.py` refuses and warns.

## When to use it

Every build, before any ad text. Ad text and customizers are in `playbooks/write-the-ads-and-customizers.md`. Owners, launch blockers and the first 14 days are in `playbooks/launch-checklist.md`. Auditing an account that already runs belongs to the account audit skill.

## What to read in the output

- From `start_build.py`: **WHAT THE ACCOUNT ALREADY HAS** (campaigns with Status, Type, Bid strategy and Daily budget; keywords with Match type, Clicks, Cost and Conversions) and **LIMITS THE CHECK ENFORCES.**
- From `check_plan.py`: **PLAN CHECK** (PASSED or REFUSED), **WHAT THE PLAN BUILDS** (match types, daily budget, the most in a day and a month), **KEYWORDS** with "Already in the account", **NEGATIVE KEYWORDS** with "Own keywords tested", and **CHECKS** and **WARNINGS** by name.

## The decisions

| What you see | What it means | What to do | Label |
|---|---|---|---|
| The brief has no places, budget or landing page | A made up value looks real in the import file. | Ask, and do not write the plan until the person answers. | Practitioner rule |
| The brief gives a radius around a place, not a list of places | Suburbs picked from memory are invented places. | Write the named place only. Tell the person to set the radius on it before posting. | Practitioner rule |
| Two services share a budget, a target and a landing page theme | One campaign, two ad groups. | Same budget and target, same campaign. Same landing page and creative theme, same ad group: both must match, so one shared page with different searches and a different message (install against repair) is still two ad groups. | Official (references/account-structure.md) |
| A service needs its own budget, places, conversion goal or message | A split earns its place only then. | Make it its own campaign, and name the reason in the campaign name. | Official (references/account-structure.md) |
| Other Search campaigns in WHAT THE ACCOUNT ALREADY HAS use Maximize Conversions or Target CPA | The account records conversions. | Start on Maximize conversions without a target, and add one once the campaign has its own conversions. Record it under assumptions. | Practitioner rule |
| Conversion recording is unknown and the account shows nothing to tell | Bidding on conversions would have nothing to learn from. | Ask. If the person says to build anyway, use Maximize clicks with exact and phrase match, and say why. | Practitioner rule |
| The conversion the brief names is an early step, such as a form start | Optimizing a lead, a booked job and a paid job are different goals. | Ask which outcome the business wants more of, and write it under primary_conversion. | Practitioner rule |
| Broad match is wanted | Google ties broad match to Smart Bidding. | Broad only with a conversion bid strategy and tracking the person confirmed. The check warns otherwise. | Official (references/keywords.md) |
| Manual CPC or Maximize clicks | AI Max search term matching does not work with Manual CPC. | Exact and phrase, and `ai_max` off. Google turns AI Max on for every new Search campaign unless the file says off, and the check warns when it is on without bidding on conversions. | Official (references/search-campaign-setup.md) |
| A keyword in KEYWORDS shows "Already in the account" | Two copies compete for the same searches. | Decide with the person which campaign keeps it. Usually the one with the conversions in WHAT THE ACCOUNT ALREADY HAS. Pause the other on launch day. | Official (references/account-structure.md) |
| The account runs Performance Max | An exact match keyword identical to the search wins over Performance Max. Phrase and broad share priority with its search themes. | Use exact match for the searches this campaign must own. | Official (references/keywords.md) |
| A niche keyword has no volume estimate | Missing data is not proof of no demand, nor of cheap demand. | Keep it if the business sells exactly that, and say it is a test. | Practitioner rule |

**Negatives, three levels** (Practitioner rule):

- **The list:** searches wrong for the whole business, such as job seekers. It applies to every campaign of the build.
- **Campaign:** searches wrong for this service, or that belong to another campaign.
- **Ad group:** sends a search to the right ad group, such as "replacement" in the repair ad group.

Before any negative, ask whether the words describe someone who wants what the business sells. "How to" is waste for a plumber and can be a customer for a business that sells guides. Negatives do not match close variants, so plural and singular each need their own (Official, references/keywords.md). A shared list reaches other campaigns: check who else uses it.

## How big a change

- **Budget:** never invented. Use the person's number. The check prints what it can reach: up to 2 times the daily budget in a day and at most 30.4 times in a month (Official, references/build-limits-and-editor-import.md). Show the person both.
- **Budget reach:** the check warns when a daily budget does not cover one click at the Max CPC, or one conversion at the target (Practitioner rule). Below that, the campaign cannot learn.
- **Ad groups:** as many as there are themes with their own landing page. Google's guidance is themed ad groups, not one keyword each (Official, references/account-structure.md). The check warns on a single keyword ad group.
- **Keywords per ad group:** no source gives a number. The close searches of the theme.
- **Launch narrow enough to learn, broad enough to gather data.** Do not split for its own sake: more segmentation can thin out the data each part learns from (Practitioner rule, references/account-structure.md).

## Failure modes

- **A name the account already uses.** Editor matches rows by name and would edit the live campaign. The check refuses it when the campaigns report was given. Ask for it.
- **A negative that blocks the build.** The check tests every negative against every keyword it can reach and refuses a block. Narrow the negative, never drop the keyword.
- **Splitting by habit.** Splitting campaigns by device or by match type is not Google's current guidance (Official, references/account-structure.md).

## Worked example

Northside Plumbing wants sewer line work in Denver and Aurora at 120.00 a day. WHAT THE ACCOUNT ALREADY HAS shows two Search campaigns on Maximize Conversions and one on Target CPA, so the account records conversions: the plan starts on Maximize conversions without a target. One campaign, "Sewer Line | Search", three ad groups by landing page: repair, replacement, camera inspection. 14 keywords: 5 exact, 9 phrase, 0 broad. The first draft was refused for "camera" in the list, which would block 2 of the build's own keywords. The final plan warns that "sewer line repair" (phrase) is already in Drain Cleaning | Search > Sewer Repair, which converts: decide who keeps it before launch.

## What to tell the client

"One new Search campaign for sewer work, split into repair, replacement and inspection so each search lands on the right page. It starts on the bidding your other campaigns already use, at 120.00 a day, which can reach 3,648.00 in a month. One keyword already runs in your drain campaign, so we choose which campaign keeps it."
