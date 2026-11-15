<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## REPORTING & DIAGNOSTICS

### Durable Diagnostic Surface Map
- Entity reads and performance reports
- Search terms and keyword diagnostics
- Change history
- Account history
- Ad preview and diagnosis
- Bid strategy reports
- Performance Planner
- Policy review and disapproval surfaces
- Conversion and value validation, including enhanced-conversion and offline-import diagnostics
- Campaign not-running or low-traffic diagnostics
- Performance Max channel performance reporting
- Feed or asset diagnostics where relevant
- Optimization score, recommendations and auto-applied recommendations

- Optimization score is Google's 0-100% estimate of how well the account is set up; applying or dismissing every recommendation both reach 100%, so treat it as a list of open suggestions, not a performance measure.
- Auto-applied recommendations are set per account and type, apply daily when relevant, never raise budgets, and show in the recommendations History tab and in Change history (API: change events with client type GOOGLE_ADS_RECOMMENDATIONS_SUBSCRIPTION). Check this before attributing an unexplained change to the team.
- Change history covers 2 years; system edits can appear as "Google Ads system" or "ads-dartsearch-budget", and some account-level and Google-representative changes may be missing. API change events cover 30 days, can lag up to three minutes and don't capture every change.
- Bid strategy status: Learning can follow a new strategy, a strategy setting change, a budget change, a composition change or a conversion setting change, but not a Target CPA or Target ROAS change. Limited can mean budget, bid limits, data, inventory, low-priority spend or low Quality Score. Misconfigured often means a Maximize strategy shares a budget with campaigns on other strategies. No statuses for Hotel campaigns.

### Investigation Order
1. Confirm serving, billing, and policy eligibility.
2. Confirm measurement and conversion semantics.
3. Confirm recent changes through change history.
4. Review performance and strategy status through official reporting surfaces.
5. Only then escalate into market pressure, competitor interpretation, or structural recommendations.

### What This Topic Is For
- Teaching the agent what diagnostic surfaces exist
- Teaching the agent how to sequence an investigation
- Teaching the agent not to jump from symptom to theory without evidence

### What This Topic Is Not For
- It is not a substitute for live account evidence.
- It does not answer current performance questions by itself; it tells the agent where to look and in what order.
- It does not turn PMax, Display, conversion, or policy diagnosis into one generic checklist; retrieve the relevant campaign or measurement topic when the symptom is specific.

### Companion Topics
- Lifecycle operations: the "Workflow Operations" reference
- Search diagnosis: the "Search Campaign Setup" reference, the "Keyword Management" reference
- Policy review: the "Risk & Compliance" reference
- Measurement checks: the "Signal Injection & Tracking" reference, the "GA4 Engineering & Truth Layer" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Feature deprecations and unversioned changes](https://developers.google.com/google-ads/api/docs/deprecations) | 2026-09-30 | 2026-10-09 |
| [Google Ads Help - About the search terms report](https://support.google.com/google-ads/answer/2472708) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - About change history](https://support.google.com/google-ads/answer/19888) | 2026-06-21 | 2026-10-14 |
| [Google Ads Help - Review your account history](https://support.google.com/google-ads/answer/2454137) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About the Ad preview and diagnosis tool](https://support.google.com/google-ads/answer/148778) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - How to find your bid strategy reports](https://support.google.com/google-ads/answer/7074568) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About Performance Planner](https://support.google.com/google-ads/answer/9230124) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About the enhanced conversions for web API diagnostics report](https://support.google.com/google-ads/answer/11954870) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About the enhanced conversions for web tag diagnostics report](https://support.google.com/google-ads/answer/11956168) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About the enhanced conversions for leads diagnostics report](https://support.google.com/google-ads/answer/15249267) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About offline conversion imports](https://support.google.com/google-ads/answer/2998031) | 2026-06-21 | 2026-10-14 |
| [Google Ads Help - How to fix Google Ads Performance Max campaign not running or low traffic](https://support.google.com/google-ads/answer/12131516) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - How to fix a Google Display Ads campaign not running or low traffic](https://support.google.com/google-ads/answer/7280809) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About the channel performance report for Performance Max](https://support.google.com/google-ads/answer/16260130) | 2026-06-21 | 2026-10-14 |
| [Google Ads Help - Disapproved: Definition](https://support.google.com/google-ads/answer/2615949) | 2026-06-21 | 2026-06-21 |
| [Google Ads Help - About optimization score](https://support.google.com/google-ads/answer/9061546) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About applying recommendations automatically](https://support.google.com/google-ads/answer/10279006) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - Optimization score and recommendations](https://developers.google.com/google-ads/api/docs/recommendations) | 2026-09-30 | 2026-10-14 |
| [Google Ads API Docs - Change Event](https://developers.google.com/google-ads/api/docs/change-event) | 2026-09-30 | 2026-10-14 |
| [Google Ads Help - About bid strategy statuses](https://support.google.com/google-ads/answer/6263057) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - BiddingStrategySystemStatus (v25)](https://developers.google.com/google-ads/api/reference/rpc/v25/BiddingStrategySystemStatusEnum.BiddingStrategySystemStatus) | 2026-07-22 | 2026-10-14 |
| [Google Ads Help - Duration of the learning period for campaigns and what affects it](https://support.google.com/google-ads/answer/13020501) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - Bid strategy status](https://developers.google.com/google-ads/api/docs/campaigns/bidding/strategy-status) | 2026-09-30 | 2026-10-14 |
