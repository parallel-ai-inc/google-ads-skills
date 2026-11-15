# How negative keywords match

Written by hand. Source: Google Ads Help, "About negative keywords", https://support.google.com/google-ads/answer/2453972. To be re-read against that page before each release.

## Official: the three negative match types

| Negative match type | It blocks a search when | Example negative | Blocks | Does not block |
|---|---|---|---|---|
| **Negative broad** | The search contains every word of the negative, in any order | running shoes | "blue running shoes", "shoes running" | "blue tennis shoes", "running shoe" |
| **Negative phrase** | The search contains the same words in the same order, with other words allowed before or after | "running shoes" | "blue running shoes", "running shoes sale" | "shoes running", "running blue shoes" |
| **Negative exact** | The search is exactly those words in that order, with nothing added | [running shoes] | "running shoes" | "blue running shoes", "running shoe" |

For a negative of one word, broad and phrase block the same searches.

## Official: what negatives do not do

- **No close variants.** A negative does not match plurals, singulars, synonyms or other expansions. Google's own example: the negative broad keyword "flowers" blocks "red flowers" but not "red flower". Add each form you want blocked.
- **Casing is ignored.** "Jobs" and "jobs" are the same negative.
- **Negative match types are not the same as keyword match types.** A negative broad keyword is far narrower than a broad match keyword.

## Not settled: misspellings

Google's negative keywords page says negatives account for misspellings. Google's Performance Max questions page says brand exclusions, unlike negative keywords, block clear misspellings. Do not present either as settled. Where misspelled brand searches matter, use brand exclusions.

## Official: where a negative applies

- **Account level:** a negative keyword list, or account level negatives, applied to campaigns. A list only works on the campaigns it is applied to.
- **Campaign level:** every ad group in that campaign.
- **Ad group level:** that ad group only.

## Practitioner rules

- Use the narrowest negative that stops the searches you mean to stop.
- Test every negative against the searches that convert and against the account's own keywords before adding it. A single word such as "free" often blocks a search that pays, such as "free estimate".
- A negative that is safe in this report can still block a good search that did not happen in this date range. Widen slowly.
- Keep negatives that are wrong for the whole business in one account level list, and campaign specific negatives on the campaign.

## What the test in this skill does

It applies the three rules above to the exact words in the report. It ignores casing. It does not model misspellings, so a negative can block slightly more in the account than the test shows.

## Limits on lists

Source: Google Ads Help, "About negative keyword lists", https://support.google.com/google-ads/answer/2453983, read 2026-11-14.

- An account can "create up to 20 negative keyword lists". When it already has 20, add the negatives to an existing list instead of making a new one.
- "You can add up to 5,000 negative keywords per list."
- Account-level negatives: "A limit of 1,000 negative keywords can be excluded for each account."
- To paste a list in Google Ads, enter one negative per line: quotation marks for phrase match, square brackets for exact match, no symbols for broad match (Google Ads Help, "About negative keywords", https://support.google.com/google-ads/answer/2453972).
- Tested 2026-11-14: this skill's list file, pasted into a new negative keyword list in the Google Ads web interface, read each line as intended: `"how to"` as phrase match, `[drain snake]` as exact match, and plain words as broad match.
