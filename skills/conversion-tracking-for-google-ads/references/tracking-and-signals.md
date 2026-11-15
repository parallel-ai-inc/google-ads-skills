<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## SIGNAL INJECTION & TRACKING

### What Google-Owned Sources Support
- Consent mode on websites should set default consent states before measurement sends data, then update consent after the user makes a choice and before page transitions.
- Consent mode v2 includes advertising data-use states such as `ad_user_data` and `ad_personalization`; do not reduce consent review to cookie storage alone.
- Enhanced conversions for leads uses hashed first-party customer data to improve offline lead attribution, but Google’s current upload direction is Data Manager API first.
- Starting June 15, 2026, Google says offline conversion imports and enhanced-conversions-for-leads uploads migrate to Data Manager API and are blocked in Google Ads API without qualifying historical upload activity or allowlisting. The restriction historically attached to developer tokens and remains in force after the move to Cloud-project access.
- Offline conversion imports have identifier, timestamp, deduplication, diagnostics, and upload-window requirements; use Google’s current guidelines before promising that a backfill or lead-import workflow will be accepted.

### Conversion Goals And Bidding Inputs (details in the claims)
- Bidding uses a conversion action only when it is Primary and in a goal the campaign uses; secondary actions (including new Google Analytics imports) only report in All conversions, except inside a custom goal.
- Goal or action changes need 1-2 conversion cycles in most cases; set budgets first. For goal migrations Google recommends gradual target changes and a Target ROAS from the previous 4 weeks excluding conversion delay.
- Conversion window changes apply going forward only. Adjustments reach Smart Bidding only within 7 days of the conversion. Value rules change both reported and bid-on value at auction time.
- Data exclusions cover tracking or upload outages (at least 90% of affected clicks plus conversion delay; not for issues older than 14 days, 60 on Shopping); don't remove one once applied.
- Some conversion Help pages warn that frequent edits reset a "7-14 day" learning period; Google's bidding pages say target changes don't trigger Learning. Read the bid strategy status.

### Signal Coverage
- Consent mode: basic mode uses a general conversion model, advanced mode sends cookieless pings and supports an advertiser-specific model; modeling starts at 700 ad clicks over 7 days per country and domain grouping.
- Data Strength guidance asks for at least 3 identifier signals per event; Google tag gateway serves tags through the advertiser's own CDN or server.
- Google Ads API import restrictions for new adopters: session attributes and IP addresses since February 2, 2026; offline imports and enhanced conversions for leads since June 15, 2026. April 2026 import improvements can lift attribution rates without a tracking fault.

### Safe Implementation Priorities
1. Confirm which identifiers are actually captured today: `gclid`, `gbraid`, `wbraid`, order IDs, lead IDs, or hashed user data.
2. Confirm consent collection, `ad_user_data`, `ad_personalization`, and tag timing before diagnosing bidding or attribution.
3. Confirm whether the workflow is a new/current Data Manager API path or a legacy/allowlisted Google Ads API upload path.
4. Validate upload timing, timezone handling, deduplication, partial failures, diagnostics, and reporting lag before assuming the import pipeline is healthy.

### Enhanced Conversions And Offline Import Guardrails
- Normalize and hash user-provided data exactly as Google documents before upload.
- Use the identifiers and user data that the chosen workflow actually supports; do not assume every path accepts the same inputs.
- Treat upload-window limits, partial-failure handling, and deduplication as product constraints, not optional niceties.
- Treat Google Ads API conversion-upload tools as legacy/compatibility execution paths unless the account and historical upload-access eligibility are verified. For new or future upload architecture, guide toward Data Manager API.
- Enhanced conversions for leads and offline import reporting are not instant; use conversion-time reporting and diagnostics before declaring success or failure.
- If the question is about the latest Data Manager or offline-import behavior, corroborate with current Help Center or developer docs before answering.

### Companion Topics
- Durable campaign setup: the "Search Campaign Setup" reference, the "App Campaign Setup" reference, the "Audiences & Customer Match" reference
- Account-specific diagnosis: the "Reporting & Diagnostics" reference
- GA4 export and MP details: the "GA4 Engineering & Truth Layer" reference

### Consent And Signal Quality
- Consent mode affects what signals Google receives and how tags behave; it is not just a cookie-banner implementation detail.
- When consent or click IDs are missing, diagnose the capture chain before blaming campaign settings or Smart Bidding.
- Use server-side tagging, first-party endpoints, or other architecture changes as implementation options, not as universal performance guarantees.
- Do not send user-provided data unless the account, consent, and implementation path satisfy the current Google policy and setup requirements.

### What Not To Present As Fact
- Do not quote generic match-rate, CPA-lift, or conversion-recovery percentages unless a live Google-owned source publishes them for the exact workflow in question; quote Google-published uplift figures only with their source and basis (internal data, simulation, averages), never as a forecast for one account.
- Do not promise that hashed data alone will fix poor consent coverage, missing click IDs, or broken primary conversions.
- Do not present one offline-conversion recipe as universal; product path, identifier availability, and country/privacy requirements change the answer.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
| [Google Ads API - Feature deprecations and unversioned changes](https://developers.google.com/google-ads/api/docs/deprecations) | 2026-09-30 | 2026-10-09 |
| [Google Ads Help - About enhanced conversions for leads](https://support.google.com/google-ads/answer/15713840) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - Guidelines for importing offline conversions](https://support.google.com/google-ads/answer/15081888) | 2026-06-20 | 2026-10-14 |
| [Google for Developers - Set up consent mode on websites](https://developers.google.com/tag-platform/security/guides/consent) | 2026-10-13 | 2026-10-14 |
| [Google Ads Help - Updates to your enhanced conversions settings](https://support.google.com/google-ads/answer/16884284) | 2026-06-20 | 2026-10-14 |
| [Google for Developers - Google Ads offline conversions](https://developers.google.com/data-manager/api/devguides/events/google-ads/offline) | 2026-06-16 | 2026-06-20 |
| [Google for Developers - Upgrade from the Google Ads API](https://developers.google.com/data-manager/api/devguides/events/google-ads/offline/upgrade) | 2026-06-16 | 2026-06-20 |
| [Google for Developers - Send events](https://developers.google.com/data-manager/api/devguides/events/send-events) | 2026-06-16 | 2026-06-20 |
| [Google Ads Data Manager Help - About Google Ads Data Manager](https://support.google.com/google-ads-data-manager/answer/13761872) | 2026-06-20 | 2026-06-20 |
| [Google Ads Help - About conversion goals](https://support.google.com/google-ads/answer/10995103) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About primary and secondary conversion actions](https://support.google.com/google-ads/answer/11461796) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Understand your conversion tracking data](https://support.google.com/google-ads/answer/6270625) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Changing conversion goals and actions used for Smart Bidding](https://support.google.com/google-ads/answer/14571185) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Change Smart Bidding strategies and change conversion goal (campaign level optimization)](https://support.google.com/google-ads/answer/14593208) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About customer lifecycle goals](https://support.google.com/google-ads/answer/12080169) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About enhanced conversions](https://support.google.com/google-ads/answer/9888656) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About consent mode](https://support.google.com/google-ads/answer/10000067) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About consent mode modeling](https://support.google.com/google-ads/answer/10548233) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Your guide to conversion modeling](https://support.google.com/google-ads/answer/12284070) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About conversion windows](https://support.google.com/google-ads/answer/3123169) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Effectively use Smart Bidding with Shopping and Performance Max campaigns](https://support.google.com/google-ads/answer/15624876) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About conversion value rules](https://support.google.com/google-ads/answer/10518330) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About conversion adjustments](https://support.google.com/google-ads/answer/7686447) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Enhance your conversion measurement and ad performance with Google tag gateway for advertisers](https://support.google.com/google-ads/answer/16214371) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Data Strength Best Practices](https://support.google.com/google-ads/answer/16517525) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About offline conversion imports](https://support.google.com/google-ads/answer/2998031) | 2026-06-21 | 2026-10-14 |
| [Google Ads Developer Blog - Changes to IP Address and Session Attribute Support in the Google Ads API](https://ads-developers.googleblog.com/2026/01/changes-to-ip-address-and-session.html) | 2026-01-07 | 2026-10-14 |
| [Google Ads Developer Blog - Upcoming Improvements to Offline Conversion Imports](https://ads-developers.googleblog.com/2026/03/upcoming-improvements-to-offline.html) | 2026-03-26 | 2026-10-14 |
| [Google Ads Developer Blog - Changes to Offline Click Conversion Import Support in the Google Ads API](https://ads-developers.googleblog.com/2026/05/changes-to-offline-click-conversion.html) | 2026-05-15 | 2026-10-14 |
