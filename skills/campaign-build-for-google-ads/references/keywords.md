<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## KEYWORD MANAGEMENT

### What Google-Owned Sources Support
- Google’s current Search guidance explicitly ties broad match to Smart Bidding rather than treating match types as isolated manual levers; broad match is the default match type, and Google calls Smart Bidding critical for it.
- Search terms reporting remains the official place to inspect what queries actually triggered ads, but low-volume queries may be omitted for privacy and search terms insights can group them into themes instead of exposing the query.
- Google's negative keyword page says negative keywords don't match close variants or other expansions (excluding the negative broad match keyword "flowers" blocks "red flowers" but not "red flower"), so synonyms and singular or plural forms must be added; the same page says negative keywords automatically account for casing and misspellings.
- AI Max Search adds keyword-adjacent search term matching, reporting, and source columns. Current Google Ads API docs expose specific controls and reporting, while Google's AI Max FAQ still carries older API/Editor caveats around activation or deactivation, text customization, and brand settings.
- Only an exact match Search keyword identical to the query (spell-corrected counts; plurals and synonyms do not) is preferred over Performance Max. Identical phrase or broad keywords, including AI Max, share the next priority with identical Performance Max search themes; then relevance and Ad Rank decide. Budget-limited Search campaigns and searches from AI Mode, AI Overviews, Lens or autocomplete can break the preference.
- Brand lists match a brand across languages and scripts; brand inclusions limit a Search campaign to the listed brands, brand exclusions block them in Search and Performance Max, and exclusions win when both apply.

### Practical Keyword Controls
- Use broad match intentionally when the conversion signal, bidding strategy, and negative-keyword governance are strong enough to absorb wider matching.
- Use search-term reviews to decide whether the issue is query quality, missing negatives, weak landing-page fit, AI Max or broad-match expansion, or bad business economics.
- Treat search terms report, search terms insights, AI Max source columns, brand inclusions, brand exclusions, and Performance Max overlap behavior as product behaviors that can change; check current docs before quoting named controls or interactions as fixed rules.

### Negative-Keyword Discipline
- Keep universal blockers, brand-protection rules, and campaign-specific negatives clearly separated.
- Use negative-keyword strategy to protect traffic quality, not to recreate perfect deterministic control over every query or to replace brand exclusions where Google recommends brand exclusions.
- In Performance Max, Google Help warns that negative keywords are restrictive and recommends brand exclusions for brand-search protection because they cover common misspellings, variants, and subsidiary brands more completely.
- If the user asks about the latest match-type or query-prioritization behavior, corroborate with current Help Center material before answering.

### What Not To Present As Fact
- Do not explain current keyword matching with fixed hidden-model or embedding stories unless a live Google-owned source states them that way.
- Do not promise fixed lift percentages from broad match or fixed spend-drift percentages from looser matching.
- Do not present misspelling coverage as settled: Google's About negative keywords page (answer/2453972) says negatives account for casing and misspellings, while its Performance Max top-questions page (answer/14587068) says brand exclusions, unlike negative keywords, block clear misspellings. Name the conflict, and use brand exclusions where misspelled brand traffic matters.
- Do not freeze current keyword prioritization into a timeless rule set; Google changes these systems.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - About the search terms report](https://support.google.com/google-ads/answer/2472708) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - About Performance Max campaigns](https://support.google.com/google-ads/answer/10724817) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - How AI Max for Search campaigns works](https://support.google.com/google-ads/answer/15910187?hl=en) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - Get started with AI Max for Search campaigns](https://developers.google.com/google-ads/api/docs/campaigns/ai-max-for-search-campaigns/getting-started) | 2026-06-10 | 2026-06-20 |
| [Google Ads Help - Your guide to broad match](https://support.google.com/google-ads/answer/12159290) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About negative keywords](https://support.google.com/google-ads/answer/2453972) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About ad group and asset group prioritization within a Google Ads account](https://support.google.com/google-ads/answer/2756257) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About brand settings for Search and Performance Max](https://support.google.com/google-ads/answer/13721847) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About negative keywords](https://support.google.com/google-ads/answer/16668865?hl=en) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - Maximize performance on Search with updates to query matching](https://support.google.com/google-ads/answer/15070437) | 2024-06-26 | 2026-10-14 |
