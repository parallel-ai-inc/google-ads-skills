# Ad customizers in responsive search ads

Written by hand. To be re-read against the source before release. Every Google page below was read on 2026-11-13. The generated references in this folder say only that Google documents customized text inside responsive search ads, so the syntax and limits are kept here with the page each comes from. Everything on this page is **Official** unless it says otherwise.

## The four codes

A code sits in curly brackets inside a headline or a description. The text after the colon is the default text, shown when nothing can be inserted.

| Code | What it inserts | Written as | Source |
|---|---|---|---|
| Keyword insertion | The ad group keyword that matched, not the search term | `{KeyWord:Default text}` | "Set up keyword insertion for your ad text", https://support.google.com/google-ads/answer/6371157 |
| Location insertion | The city, state or country from the campaign's location targeting | `{LOCATION(City):Default text}`, with City, State or Country | "About location insertion for responsive search ads", https://support.google.com/google-ads/answer/9773001, and the Google Ads API guide below |
| Countdown | Days, then hours, then minutes to an end time | `{COUNTDOWN(yyyy-MM-dd HH:mm:ss,daysBefore)}` or `{GLOBAL_COUNTDOWN(yyyy-MM-dd HH:mm:ss,daysBefore)}` | "Highlight upcoming events with countdowns", https://support.google.com/google-ads/answer/6193743 |
| Ad customizer | A value the advertiser sets for an attribute, such as a price | `{CUSTOMIZER.AttributeName:Default text}` | Google Ads API, "Responsive search ad (RSA) customization", https://developers.google.com/google-ads/api/docs/ads/customize-responsive-search-ads, and "Create ad customizers for responsive search ads", https://support.google.com/google-ads/answer/10711524 |

## Keyword insertion

- The capitals of the code set the capitals of the keyword shown: `keyword` gives "dark chocolate", `Keyword` gives "Dark chocolate", `KeyWord` gives "Dark Chocolate", `KEYWord` gives "USA Chocolate", `KeyWORD` gives "Chocolate Made In USA".
- When the keyword is too long to fit the line's limit, the default text shows instead. Google's example: "gourmet chocolate truffles" is too long, so "Chocolate" shows.
- The code can go in headlines, descriptions and the display path. It cannot go in the Final URL. Keep the default text short enough to stay inside the limit.
- It works the same on every match type, and shows the keyword, not the search term.
- The inserted text must still read well and follow policy. Trademarks restricted under Google's trademark policy are not inserted. It cannot be used for healthcare and sexual content.
- From "About applying recommendations automatically" (https://support.google.com/google-ads/answer/10279006): search terms not covered by negative keywords can appear in ad text through keyword insertion.

## Location insertion

- One location code in a headline and up to 2 in descriptions. The page does not say whether that is per line or per ad. This skill applies it per line.
- At least 3 headlines without location insertion, or the location codes need default text.
- The location comes from the campaign's location targeting, so the level (City, State or Country) must fit those locations. With DMA targeting the closest city is used. State does not work for other countries' provinces or regions.
- Use the capitals as written: `LOCATION`, `City`, `State`, `Country`.

## Countdown

- `COUNTDOWN` and `GLOBAL_COUNTDOWN` both count down by day, then hour, then minute.
- `daysBefore` is how many days before the end the countdown starts to show. Left blank in the Google Ads editor, it is 5. Days are counted as midnights.
- The countdown text can be 8 characters long. Leave room for it.
- At least 3 headlines without a countdown, or use default text. The RSA countdown code has no default text, so this skill asks for 3 headlines without one.
- An ad with a countdown stops showing after the end date. Change or unpin the headline when the countdown is over.
- Countdowns cannot go in the display path.
- The language follows the ad's language. It cannot be set for responsive search ads.
- **The pages disagree on time zones.** The Help page says `COUNTDOWN` uses the time zone of the person searching and `GLOBAL_COUNTDOWN` the account's time zone. The API guide says the opposite. Check the setting in Google Ads before relying on either.

## Ad customizers

- An attribute has a name and a data type: Text (any letters, numbers or symbols), Number (any number, decimals allowed), Price (a number with valid currency characters, such as $24.99, with no space between the number and the currency) or Percent (a number with a percent sign).
- An attribute name must not start with an underscore or contain symbols, punctuation or special characters. Such names may get ads disapproved. Names are unique, ignoring capitals.
- An account can have up to **40** enabled customizer attributes.
- Values are set at the account, campaign, ad group or keyword level. The most specific wins, in this order: keyword, ad group, campaign, account, then the default text.
- **An ad that uses a customizer with no value anywhere cannot be reviewed.** Create the attribute and give it a value before the ad goes in.
- Values can be set by hand (Tools, Business data, Ad customizer attributes) or uploaded from a spreadsheet (Tools, Bulk actions, Uploads), where value columns are headed `Customizer:` plus the attribute name, such as `Customizer:Price`. Keyword and ad group values need the Campaign and Ad group columns. `remove_value` clears a value so the default shows.
- Values go through ad review.

## Limits that apply to every code

- The text that shows, the inserted value or the default text, must fit the line's limit: 30 characters for a headline and 90 for a description. If the inserted value is too long or fails to validate, the default text is used, as long as it fits. (API guide above; the limits are in `build-limits-and-editor-import.md`.)
- No code in the Final URL. ("Set up keyword insertion", above.)
- **The pages disagree on display paths.** Help pages allow keyword insertion, location insertion and business data customizers in the display path, and not countdowns. The API guide says replacements happen in headlines and descriptions, not in display URLs.
- The IF function is not supported in responsive search ads. ("Create responsive search ads with customized text", https://support.google.com/google-ads/answer/11559472)
- The old text ad forms, with an equals sign and quotation marks such as `{=COUNTDOWN("...")}`, are not the responsive search ad forms.

## Tested in Google Ads Editor 2.14.2 on 2026-11-14

- An import kept `{KeyWord:Sewer Repair}`, `{LOCATION(City):Denver}`, `{COUNTDOWN(2026-12-31 23:59:00,5)}` and `{CUSTOMIZER.Price:Free}` exactly as written, with no error.
- Editor's character count puts the default text in place of a keyword, location or customizer code, as this skill does. It counts a countdown as nothing; this skill counts it as 8, as Google's page says, so the skill is the stricter of the two.
- Editor did not flag a customizer attribute that does not exist in the account. Create every attribute in Google Ads before posting.

## Not documented by Google

- Whether a customizer attribute can be created by an Editor import. This skill assumes it cannot: create it in Google Ads first.

## Practitioner rules

- Give every keyword, location and customizer code default text, so the line can be counted and always shows words.
- Write the default text as a real phrase that makes sense in the headline on its own.
- Use keyword insertion only in ad groups whose keywords all read well in the sentence. One awkward keyword shows awkwardly.
- A countdown needs a real date the business stands behind, such as a sale end date. Never invent one.
