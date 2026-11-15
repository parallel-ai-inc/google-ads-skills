<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## GOOGLE ADS API ENUMS & STATUS VALUES

### What This Topic Covers
- Campaign-family enum values such as advertising channel type
- Status enums such as enabled, paused, and removed

### Safe Enum Interpretation
- Enums are version-sensitive. Use the active API version reference when precision matters.
- Presence of an enum does not prove current eligibility. A campaign type or strategy can exist in the enum set while still being unavailable to the current account or workflow.
- Removed-style statuses should be treated as terminal unless the current reference or workflow explicitly says otherwise.

### Common Durable Examples
- Advertising channel type separates Search, Display, Shopping, Video, App, Local, Hotel, Travel, Performance Max, and Demand Gen families.
- Campaign, ad group, and ad statuses distinguish currently serving, paused, removed, and return-only unknown states.
- Keyword match-type enums are structural controls, while current query-matching behavior still depends on the present product rules.
- Bidding-strategy enums can include legacy or deprecated states that still appear in API reads.

### What Not To Present As Fact
- Do not infer feature eligibility only from enum presence.
- Do not assume numeric enum values are stable across contexts unless the active reference confirms them.
- Do not describe deprecated enum states as recommended modern defaults.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-09.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Feature deprecations and unversioned changes](https://developers.google.com/google-ads/api/docs/deprecations) | 2026-09-30 | 2026-10-09 |
| [Google Ads API RPC Reference v25 - AdvertisingChannelType](https://developers.google.com/google-ads/api/reference/rpc/v25/AdvertisingChannelTypeEnum.AdvertisingChannelType) | 2026-07-22 | 2026-10-09 |
| [Google Ads API RPC Reference v25 - CampaignStatus](https://developers.google.com/google-ads/api/reference/rpc/v25/CampaignStatusEnum.CampaignStatus) | 2026-07-22 | 2026-10-09 |
| [Google Ads API RPC Reference v25 - KeywordMatchType](https://developers.google.com/google-ads/api/reference/rpc/v25/KeywordMatchTypeEnum.KeywordMatchType) | 2026-07-22 | 2026-10-09 |
| [Google Ads API RPC Reference v25 - BiddingStrategyType](https://developers.google.com/google-ads/api/reference/rpc/v25/BiddingStrategyTypeEnum.BiddingStrategyType) | 2026-07-22 | 2026-10-09 |
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
