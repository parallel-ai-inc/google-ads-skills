# Launch checklist

Campaign build: Northside Plumbing. Built from the plan checked on 2026-11-13.

Everything in the import file is paused. Nothing serves until a person enables it, on launch day, after every Stop launch item reads Said yes.

## Stop launch

Each of these blocks the launch until it reads Said yes. Only the person can answer yes.

- [x] **The conversion action named in the brief is recording conversions. "Sewer Line | Search" bids on conversions (Maximize conversions), so it has nothing to learn from without it.** Owner: Lee. In Google Ads: Goals, Conversions, All conversions. Find the conversion action and check that it has recorded recent conversions. Status: Said yes. (Practitioner rule: references/campaign-launch.md)
- [x] **Billing is set up and the payment method works.** Owner: Dana. In Google Ads: Billing, Summary. Check there is no payment alert on the account. Status: Said yes. (Practitioner rule: references/campaign-launch.md)
- [ ] **Every final URL loads on mobile and on desktop, and matches its ad group.** Owner: Not assigned. Open each final URL on the Ads sheet of the workbook on a phone and on a computer. Check the page offers what the ad offers. Status: Open: not answered. (Practitioner rule: references/campaign-launch.md)
- [x] **The budget holder approved the daily budget and what it can add up to in a month.** Owner: Dana. Show the budget holder the daily budget and the monthly spending limit on the Campaigns sheet, and get a yes in writing. Status: Said yes. (Practitioner rule: references/campaign-launch.md)
- [x] **The business confirmed the locations.** Owner: Dana. Read the locations on the Campaigns sheet to the business and confirm they are the places it serves. Status: Said yes. (Practitioner rule: references/campaign-launch.md)
- [ ] **The business approved the ad text.** Owner: Dana. Send the Ad text sheet to the business. Every claim, price and offer in it must be true. Status: Open: answered no. (Practitioner rule: references/campaign-launch.md)
- [ ] **Every warning from the plan check is decided with the person (2 warnings).** Owner: Sam. Read the Warnings sheet of the workbook. Write the decision beside each one. (Practitioner rule: references/campaign-launch.md)

## Import and review in Google Ads Editor

- [ ] **Import build-for-google-ads-editor.csv.** Owner: Sam. In Google Ads Editor: Account, Import, From file. Check the column headers Editor shows, then import. (Official: references/build-limits-and-editor-import.md)
- [ ] **Read every error and warning Editor lists.** Owner: Sam. Fix a problem in plan.json, run the check and the write step again, and import the new file. The workbook then still matches what is posted. (Official: references/build-limits-and-editor-import.md)
- [ ] **Count the proposed changes: 1 campaign, 2 locations, 3 ad groups, 14 keywords, 4 negative keywords and 4 responsive search ads.** Owner: Sam. Review imported changes. Imported rows arrive as proposed changes and nothing reaches the account until it is posted. (Official: references/build-limits-and-editor-import.md)
- [ ] **Every campaign, ad group, keyword and ad shows Paused.** Owner: Sam. Sort each view in Editor by status. Nothing in the file is set to serve. (Practitioner rule: references/build-limits-and-editor-import.md)
- [ ] **Every location is resolved.** Owner: Sam. A location typed by name must be resolved before posting. An unresolved location shows a yellow warning. (Official: references/build-limits-and-editor-import.md)
- [ ] **AI Max is off for Sewer Line | Search, as the plan chose.** Owner: Sam. Google turns AI Max on for every new Search campaign unless the file says off. This file says off. Check it reads Disabled in Editor. (Official: references/build-limits-and-editor-import.md)
- [ ] **The EU political ads declaration is right.** Owner: Sam. The file declares that each campaign doesn't have EU political ads, because Google Ads will not post a campaign without the declaration. If a campaign carries political content as Google defines it for the EU, change the declaration in Editor before posting. (Official: references/build-limits-and-editor-import.md)
- [ ] **Campaign "Sewer Line | Search": networks read Google Search, bid strategy reads Maximize conversions.** Owner: Sam. Open the campaign settings in Editor and compare them with the Campaigns sheet. (Practitioner rule: references/build-limits-and-editor-import.md)
- [ ] **Add the negative keyword list "Northside | Never relevant" (5 keywords) and apply it to every new campaign.** Owner: Sam. Paste negative-keyword-list.txt into a negative keyword list in Google Ads, then apply the list to each campaign of this build. Quotation marks mean phrase match and square brackets mean exact match. (Practitioner rule: references/build-limits-and-editor-import.md)
- [ ] **Keep the proposed changes and post.** Owner: Sam. Keep proposed changes, then post. Afterwards check in Google Ads that every campaign of this build still reads Paused. (Official: references/build-limits-and-editor-import.md)

## Launch day

- [ ] **Every Stop launch item reads Said yes.** Owner: Sam. Read the first section of this checklist. One open item means no launch. (Practitioner rule: references/campaign-launch.md)
- [ ] **Open every final URL on a phone and on a computer.** Owner: Not assigned. Use the Ads sheet. Each page must load and offer what its ad offers. (Practitioner rule: references/campaign-launch.md)
- [ ] **No ad or keyword is disapproved in Google's policy review.** Owner: Sam. In Google Ads, read the status of each ad and keyword after posting. (Practitioner rule: references/campaign-launch.md)
- [ ] **Enable ads, keywords and ad groups, then enable the campaign last.** Owner: Sam. Enable in that order, so nothing serves half built. (Practitioner rule: references/build-limits-and-editor-import.md)
- [ ] **Write down the hypothesis, the success metric and the early warning sign.** Owner: Sam. Hypothesis: Searches for sewer line repair, replacement and inspection in Denver and Aurora book jobs at a cost the business can carry, kept apart from drain cleaning. Success metric: Booked sewer appointments and cost per booking over the first 30 days. Early warning: Spend with no bookings after 14 days, or search terms about septic tanks or drain cleaning. (Practitioner rule: references/campaign-launch.md)

## First 14 days

- [ ] **Serving: every campaign is eligible to serve.** Owner: Sam. Check campaign status in Google Ads on day 1 and day 2. (Practitioner rule: references/campaign-launch.md)
- [ ] **Pacing: one day can spend up to 240.00 and one month is charged at most 3,648.00 for this build.** Owner: Sam. That is the total daily budget of 120.00 times 2 and times 30.4. Compare cost each day with these limits. (Official: references/build-limits-and-editor-import.md)
- [ ] **Tracking: the conversions this build is judged on are recorded.** Owner: Lee. The brief says: Booked appointment (online booking form). In Google Ads: Goals, Conversions, All conversions. Then check the campaign's Conversions column. (Practitioner rule: references/campaign-launch.md)
- [ ] **Search terms: read the search terms report and exclude what is plainly wrong.** Owner: Sam. If AI Max is on, Google says to wait at least 2 weeks after enabling before changes such as adding negatives. (Practitioner rule: references/campaign-launch.md)
- [ ] **Make one strategic change at a time.** Owner: Sam. Do not stack changes while the first signals form. Check conversion delay and low volume before calling a failure. (Practitioner rule: references/campaign-launch.md)

## Warnings from the plan check

Decide each one with the person before launch.

- Build: 2 of 3 ad groups have one responsive search ad: "Sewer Line Replacement", "Sewer Camera Inspection". Google's tip is at least 2 in each ad group. One is enough to launch. Add a second when there is a different message to test.
- Campaign "Sewer Line | Search" > Ad group "Sewer Line Repair" > Keyword "sewer line repair": The account already has this keyword with the same match type: campaign "Drain Cleaning | Search", ad group "Sewer Repair" (Enabled). Two copies compete for the same searches. Decide which one keeps the search, and pause the other when this build goes live.
