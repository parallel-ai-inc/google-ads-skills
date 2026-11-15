<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## SEARCH CAMPAIGN SETUP

### Required Foundations
- Define the business goal, primary conversion, geo scope, language, budget, and bid strategy before you decide how granular the campaign should be.
- Search campaigns depend on keyword coverage, negative strategy, Search ads or compatible asset-based creative, and a final URL or landing-page destination that matches the query intent.
- Search reporting and diagnostics rely on search terms, keyword state, asset coverage, conversion tracking, and current bid strategy status.

### Normal Setup Inputs
| Area | What matters |
|------|--------------|
| Goal and measurement | Primary conversion, value model, attribution implications, offline-import needs |
| Coverage | Keywords, match types, negatives, geo, schedule, device and audience layering (manual language targeting is retired for Search; see below) |
| Creative | Search ad assets, sitelinks/callouts/other assets, policy-safe final URLs |
| Bidding | Manual or Smart Bidding family, budget model, portfolio vs campaign-level strategy |
| Guardrails | Brand vs non-brand separation where it changes economics, exclusions, approval risk |

### Normal Operations
- Create or update campaigns, ad groups, ads, keywords, negatives, budgets, and assets.
- Diagnose through search terms, status, change history, landing-page review, and bid strategy reports.
- Pause, remove, copy, clone, or batch-edit only after you understand what shared budgets, portfolio strategies, and labels are attached.

### Overlap / Priority Rules
- Only a Search keyword in exact match that is identical to the query is preferred over Performance Max; identical phrase or broad keywords (including AI Max) share the next priority with identical Performance Max search themes, then relevance and Ad Rank decide. A budget-limited Search campaign and searches from AI Mode, AI Overviews, Lens or autocomplete can break that preference.
- Broad-match behavior, negative coverage, and search-term visibility evolve over time. Treat the durable structure as stable, but corroborate current control behavior when the user asks for the latest rule.

### AI Max And Legacy DSA Transition
- AI Max is a setting inside a Search campaign, on by default for new Search campaigns. Turning it on turns on search term matching, and operators can toggle search term matching off at the ad-group level. Google says AI Max features require conversion-based Smart Bidding to function effectively, and search term matching doesn't work with Manual CPC.
- Asset optimization turns on text customization and Final URL expansion at the campaign level. Final URL expansion requires text customization, and pinned RSA assets are not respected if Google chooses a more relevant URL.
- Before enabling: Google says AI Max won't be effective while the campaign is limited by budget. After enabling: wait at least 2 weeks before changes such as adding negatives. Turning AI Max off also switches off its brand exclusions and ignores its URL rules.
- Campaigns migrated in September 2026 kept equivalent settings rather than the full AI Max suite, so read each campaign's settings.
- Current Google Ads API docs and the installed client's package metadata expose specific AI Max controls, including campaign enable/disable, campaign asset automation settings, ad-group search-term matching disablement, text guidelines, page-feed inclusion criteria, and AI Max reporting. Help and API documentation cover different surfaces; verify the exact operation, supported tool, and account eligibility before any mutation.
- Before enabling AI Max with Final URL expansion, verify tracking-template compatibility because dynamic landing pages can break when `{lpurl}` handling is wrong.
- Google's June 11, 2026 DSA update scheduled DSA sunset and auto-upgrade for February 2027 and scheduled automatic AI Max upgrades for campaigns using Automatically Created Assets or campaign-level broad match for September 1–30, 2026. Do not assume a specific campaign's state from that schedule: from API v25.1, each campaign's `aca_migration_date_time` and `broad_match_migration_date_time` (output only, in the account's time zone) record when that campaign was migrated, so read them from the account. Treat new DSA creation as a legacy/transition surface, not the preferred growth path.

### Retired Search Settings
- Manual language targeting (campaign language criteria) is no longer supported for Search campaigns or AI Max for Search campaigns from September 2026; adding or updating it on a Search campaign fails with `OPERATION_NOT_PERMITTED_FOR_CONTEXT`. Performance Max keeps the setting for its other channels, but it no longer limits Performance Max ads shown on Google Search. Legacy language criteria can still be read; do not offer to add or change them on Search.
- Enhanced CPC is no longer available for Search and Display campaigns (from March 31, 2025). For Search, standard target-based bidding uses Maximize Conversions with a target CPA or Maximize Conversion Value with a target ROAS; other campaign types have their own documented strategy rules (see the "Smart Bidding Architecture" reference).

### Reporting / Diagnostic Surfaces
- Search terms, keyword reads, AI Max match/source context where available, asset performance, landing-page review, Quality Score diagnostics, bid strategy reports, and change history are the core surfaces.

### What Not To Present As Fact
- Do not treat any one account structure doctrine as the universal Google way to build Search.
- Do not present current keyword-control behavior from memory when Help Center wording or rollout state could have changed.

### Companion Topics
- Query control: the "Keyword Management" reference
- Search creative: the "Creative Engineering" reference
- Signal wiring: the "Signal Injection & Tracking" reference
- Lifecycle actions: the "Workflow Operations" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Feature deprecations and unversioned changes](https://developers.google.com/google-ads/api/docs/deprecations) | 2026-09-30 | 2026-10-09 |
| [Google Ads API - Campaign](https://developers.google.com/google-ads/api/reference/rpc/v25/Campaign) | 2026-08-17 | 2026-10-09 |
| [Google Ads Help - About the Google Search Network](https://support.google.com/google-ads/answer/1722047) | 2026-03-18 | 2026-04-03 |
| [Google Ads Help - Create effective Search ads](https://support.google.com/google-ads/answer/6167122) | 2026-03-18 | 2026-04-03 |
| [Google Ads Help - About the search terms report](https://support.google.com/google-ads/answer/2472708) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - How AI Max for Search campaigns works](https://support.google.com/google-ads/answer/15910187?hl=en) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - Get started with AI Max for Search campaigns](https://developers.google.com/google-ads/api/docs/campaigns/ai-max-for-search-campaigns/getting-started) | 2026-06-10 | 2026-06-20 |
| [Google Ads Help - About ad group and asset group prioritization within a Google Ads account](https://support.google.com/google-ads/answer/2756257) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Set up AI Max for Search campaigns](https://support.google.com/google-ads/answer/15909989) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Frequently asked questions about AI Max for Search campaigns](https://support.google.com/google-ads/answer/15913066) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About reporting in AI Max for Search campaigns](https://support.google.com/google-ads/answer/16470459) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About AI Max experiments](https://support.google.com/google-ads/answer/16450159) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About AI Max for Search campaigns](https://support.google.com/google-ads/answer/15910366) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Use text guidelines with Performance Max and Search campaigns (beta)](https://support.google.com/google-ads/answer/16489313) | 2026-10-14 | 2026-10-14 |
| [Google Ads Developer Blog - Migrate campaign-level broad match and automatically created assets to AI Max](https://ads-developers.googleblog.com/2026/08/migrate-campaign-level-broad-match-and.html) | 2026-08-12 | 2026-10-14 |
| [Google Ads Help - Maximize performance on Search with updates to query matching](https://support.google.com/google-ads/answer/15070437) | 2024-06-26 | 2026-10-14 |
| [Google Ads & Commerce Blog - AI Max Turns 1 with new ways to steer performance and expansion to more advertisers](https://blog.google/products/ads-commerce/ai-max-new-features/) | 2026-04-30 | 2026-10-14 |
| [Google Ads & Commerce Blog - We're upgrading Dynamic Search Ads to AI Max](https://blog.google/products/ads-commerce/dsa-upgrade-to-ai-max-2026/) | 2026-06-11 | 2026-10-14 |
| [Google Ads & Commerce Blog - Make AI Max work for your business with new testing and planning tools](https://blog.google/products/ads-commerce/ai-max-testing-planning-tools/) | 2026-08-20 | 2026-10-14 |
