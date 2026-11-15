<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## TECHNICAL INTEGRATION & APIs

### What Google-Owned Sources Support
- Google Ads API release notes and versioning docs are the canonical source for what changed, when it changed, and when versions sunset.
- Measurement Protocol and offline conversion docs are the canonical source for integration payload requirements and upload guardrails.
- Developer docs should outrank old snippets, migration notes, or remembered behavior whenever a technical detail matters.
- The feature deprecations page lists unversioned changes that apply to every API version, such as retired creation paths and retired targeting settings. Check it alongside the release notes.
- Developer tokens were sunset on September 9, 2026. API access levels now come from the Google Cloud project that owns the OAuth client or service account. Sending the developer-token header is optional and ignored, and existing code keeps working unchanged; Google says a future major version will start rejecting the header. This is not a credential outage.

### Practical Integration Rules
1. Check release notes and versioning before assuming an API surface or field still exists.
2. Validate measurement payloads and conversion uploads against current docs, not just against old examples.
3. Keep offline conversion answers anchored to current timing windows and migration guidance; legacy upload flows are not the default answer anymore.
4. Keep integration answers explicit about which system owns the data: Google Ads, GA4, BigQuery, CRM, or Merchant Center.
5. Treat code snippets and migration checklists as subordinate to current developer docs.
6. Measurement Protocol remains operational, but Data Manager API is the current Google-documented future-ingestion direction for server-to-server event integrations.

### What Not To Present As Fact
- Do not promise that a legacy example still works if the release notes or versioning docs say otherwise.
- Do not quote server-side match-rate improvements as universal integration outcomes.
- Do not turn Google’s current developer guidance into a long-lived invariant without checking release-sensitive docs first.

### Companion Topics
- API orientation: the "API Services Reference" reference, the "Google Ads API Enums & Status Values" reference
- Tracking and conversion setup: the "Signal Injection & Tracking" reference, the "GA4 Engineering & Truth Layer" reference
- Workflow execution: the "Workflow Operations" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-09.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Sunset dates](https://developers.google.com/google-ads/api/docs/sunset-dates) | 2026-09-30 | 2026-10-09 |
| [Google Ads API - Feature deprecations and unversioned changes](https://developers.google.com/google-ads/api/docs/deprecations) | 2026-09-30 | 2026-10-09 |
| [Google Ads API - Developer token sunset](https://developers.google.com/google-ads/api/docs/api-policy/developer-token) | 2026-10-07 | 2026-10-09 |
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
| [Google Ads API Docs - Versioning](https://developers.google.com/google-ads/api/docs/concepts/versioning) | 2026-10-06 | 2026-10-09 |
| [Google Analytics Developers - Measurement Protocol reference](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference) | 2026-06-08 | 2026-06-20 |
| [Google Ads Help - Guidelines for importing offline conversions](https://support.google.com/google-ads/answer/15081888) | 2026-06-20 | 2026-10-14 |
