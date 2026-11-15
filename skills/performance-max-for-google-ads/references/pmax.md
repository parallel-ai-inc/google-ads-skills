<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## PERFORMANCE MAX ARCHITECTURE

### Durable Setup Model
- Performance Max is a goal-based, multi-inventory campaign type (YouTube, Display, Search, Discover, Gmail, Maps) built around conversion goals, creative and landing-page inputs, and optional retail feed context.
- Which campaign serves: only a Search keyword in exact match identical to the query is preferred over Performance Max. Identical phrase or broad keywords (including AI Max) share the next priority with identical search themes; then relevance, then Ad Rank. A budget-limited Search campaign lets Performance Max occasionally serve on exact terms, and searches from AI Mode, AI Overviews, Lens or autocomplete aren't treated as identical. Against Display, Demand Gen, AI Max or another Performance Max campaign, the highest Ad Rank serves.
- Retail Performance Max depends on Merchant Center linkage and feed state in ways that non-retail Performance Max does not.

### Documented Search Controls
- Search themes (up to 50) tell the campaign what customers search for that the site, assets and feeds don't already show; search terms insights show whether a query came from a theme or keywordless targeting, and a usefulness indicator flags themes that add nothing.
- Brand exclusions block brand terms, misspellings and subsidiary brands on Search and Shopping ads (Shopping can be allowed to keep serving); Google prefers them over negatives for brand protection.
- Negative keywords work on Search and Shopping inventory only, up to 10,000 per campaign and 1,000 at account level, with no close-variant matching. Block Display and video placements through excluded content keywords in content suitability instead.
- Final URL expansion can send a search to a more relevant page and write a matching headline. URL exclusions only work while it is on; turning it off and attaching a page feed restricts serving to listed pages. Google's baseline is Final URL expansion on plus search themes.

### Targeting Controls
- Device and age targeting are full Performance Max controls (Google, August 2025), so excluding an age range or limiting device types is a real campaign setting; gender controls were announced as a beta then. Campaign-level negative keyword lists can also be applied.
- Audience signals are suggestions, not targeting; reaching only new customers needs the new customer acquisition goal.

### Reading Results
- Performance Max optimizes for marginal return across channels, so average CPA or ROAS by channel can mislead; judge the campaign against its goal and use the channel performance report and its diagnostics to find limits and creative gaps.
- The Performance Max search terms report shows queries with landing pages and ad format from March 2023 onward; placement reports are for brand safety, not performance evaluation.

### Change Windows
- Run a new campaign at least 6 weeks, avoid frequent budget, bid strategy or status changes early, and allow 1-2 weeks or one full conversion cycle after a significant change (lead generation can need up to 6 weeks).
- Since August 17, 2026 budget-limited Target CPA and Target ROAS campaigns, Performance Max included, deliver toward the stated target and may shift channel mix; Google doesn't change targets or budgets itself.
- Google data scientists report only about half of Performance Max conversions land inside the 30-day click and 3-day engaged-view windows, so short reads understate it.

### Safe Performance Max Framing
- Use account evidence from the available reporting and settings surfaces before making strong claims about what the campaign is buying or how it is governed.
- Keep retail/feed context, governance settings, and landing-page behavior in view when diagnosing performance.
- Google's GML 2026 bidding post (May 7, 2026) calls Smart Bidding Exploration for Performance Max a beta, while Help still documents it for Search with Target ROAS only, so do not promise universal account availability.
- Google's April 30, 2026 AI Max announcement says AI Max for Shopping can transform Merchant Center feeds into dynamic Shopping ads and that related conversational-query behavior is also coming to Performance Max; treat that as rollout-sensitive direction, not as proof every PMax account has the feature today.

### What To Check First
1. Campaign goal and conversion semantics
2. Feed health when the campaign depends on product data
3. Governance or exclusion evidence when overlap or brand cannibalization is a concern
4. Available reporting and landing-page evidence before rewriting the campaign story

### What Not To Present As Fact
- Do not present one exclusion hack or inventory workaround as a universal Performance Max fix.
- Do not treat the documented controls as frozen; the betas (Smart Bidding Exploration for Performance Max, AI Brief, conversational Shopping behavior, the long-term demand reporting pilot) stay rollout-sensitive.
- Do not reduce Performance Max to “Search plus assets”; the product has its own control and reporting surfaces.
- Do not turn GML blog rollout language into live-account fact; use current Help/API docs or live account evidence before claiming a specific Smart Bidding Exploration, AI Max, reporting, or experiment control is usable.
- Quote Performance Max asset limits from the sourced Google Ads API asset requirements in the "Creative Engineering" reference (checked 2026-10-19), and check the account's asset group for what is actually there.

### Companion Topics
- Retail feed interplay: the "Shopping Campaign Excellence" reference, the "Feed Optimization" reference
- Asset requirements: the "Creative Engineering" reference, the "Ad Specs & Platform Limits" reference
- Current account evidence: the "Reporting & Diagnostics" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-19.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Campaign](https://developers.google.com/google-ads/api/reference/rpc/v25/Campaign) | 2026-08-17 | 2026-10-09 |
| [Google Ads API - Performance Max asset requirements](https://developers.google.com/google-ads/api/performance-max/asset-requirements) | 2026-10-15 | 2026-10-19 |
| [Google Ads Help - About Performance Max campaigns](https://support.google.com/google-ads/answer/10724817) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - How to use brand suitability features in Performance Max](https://support.google.com/google-ads/answer/13607727) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About the search terms report](https://support.google.com/google-ads/answer/2472708) | 2026-06-20 | 2026-10-14 |
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
| [Google Ads Help - About ad group and asset group prioritization within a Google Ads account](https://support.google.com/google-ads/answer/2756257) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - How Performance Max interacts with other campaigns in your account](https://support.google.com/google-ads/answer/13810170) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Answering Your Top Questions About Performance Max](https://support.google.com/google-ads/answer/14587068) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Optimization tips for Performance Max campaign for all business types](https://support.google.com/google-ads/answer/11385582) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Changes to target based bid strategies](https://support.google.com/google-ads/answer/17061251) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About brand exclusions (Performance Max)](https://support.google.com/google-ads/answer/16669487) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Negative keywords in Performance Max campaigns](https://support.google.com/google-ads/answer/15726455) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About search themes (Performance Max)](https://support.google.com/google-ads/answer/16669486) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Final URL expansion (asset optimization)](https://support.google.com/google-ads/answer/16672777) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Common AI-based controls combinations for Performance Max](https://support.google.com/google-ads/answer/16672522) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Optimization tips for channel performance](https://support.google.com/google-ads/answer/16286939) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About the channel performance report for Performance Max](https://support.google.com/google-ads/answer/16260130) | 2026-06-21 | 2026-10-14 |
| [Google Ads Help - About the search terms report in Performance Max](https://support.google.com/google-ads/answer/16327396) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Understanding costs in Performance Max campaigns](https://support.google.com/google-ads/answer/15899323) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Optimization tips for Performance Max campaigns for lead generation](https://support.google.com/google-ads/answer/13775965) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Unlock more visibility and control in Performance Max](https://support.google.com/google-ads/answer/16451273) | 2025-08-07 | 2026-10-14 |
| [Think with Google - Creative in Performance Max Playbook](https://www.thinkwithgoogle.com/_qs/documents/18344/Google_UKI___Creative_in_Performance_Max_Playbook.pdf) | 2026-03-18 | 2026-04-03 |
| [Google Ads & Commerce Blog - Kick off 2025 with new Performance Max features](https://blog.google/products/ads-commerce/new-performance-max-features-2025/) | 2025-01-23 | 2026-04-03 |
| [Google Ads & Commerce Blog - New AI-powered bidding and budgeting innovations in Search and Shopping](https://blog.google/products/ads-commerce/bidding-budgeting-google-marketing-live-2026/) | 2026-05-07 | 2026-10-14 |
| [Google Ads & Commerce Blog - AI Max Turns 1 with new ways to steer performance and expansion to more advertisers](https://blog.google/products/ads-commerce/ai-max-new-features/) | 2026-04-30 | 2026-10-14 |
| [Google Ads & Commerce Blog - We're upgrading Dynamic Search Ads to AI Max](https://blog.google/products/ads-commerce/dsa-upgrade-to-ai-max-2026/) | 2026-06-11 | 2026-10-14 |
| [Google Ads Developer Blog - Announcing v25.2 of the Google Ads API](https://ads-developers.googleblog.com/2026/09/announcing-v252-of-google-ads-api.html) | 2026-09-23 | 2026-10-14 |
| [Think with Google - Addressing the growth gap: The hidden ROI of demand creation](https://www.thinkwithgoogle.com/next/article/measurement/demand-creation-marketing-roi/) | 2026-02-01 | 2026-10-14 |
