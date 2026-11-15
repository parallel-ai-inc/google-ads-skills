<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## API SERVICES REFERENCE

### What This Topic Is For
- Orienting the agent to Google Ads API service families and object relationships
- Explaining where versioning, release notes, quotas, enums, and resource references fit
- Helping the agent reason about operations at a conceptual level before it relies on exact field metadata or live tooling

### Durable Service Families
- Campaign and asset management
- Criteria and targeting management
- Audience and customer-list management
- Conversion upload and adjustment services
- Reporting and GAQL-based reads
- Batch jobs and bulk mutation workflows

### Safe API Reasoning Rules
1. Use this topic to explain which kind of service or operation family applies.
2. Use current developer docs, field metadata, or tool schemas when the answer depends on an exact method, field, or enum.
3. Minor versions can add backward-compatible changes without changing the endpoint, so check release notes before assuming the currently active surface is frozen.
4. Check versioning and release notes before assuming a service or field still behaves the way an older snippet suggests.
5. Treat the latest release-note additions as current API orientation, not live-account eligibility proof. Version-specific history (for example what v24.1 added) stays history.
6. BatchJobService is the async/bulk-operation surface for mixed-service operations, transient retries, temporary IDs, and partial-failure behavior, but unsupported atomic operations still need the documented mutate path.
7. Separate three questions: what the live API exposes, what my installed client library can encode, and whether I have an active tool for it. A minor version can make a field readable through reporting before the installed client can write it, and an API field is never proof that I can change it.
8. Some platform changes are unversioned and apply to every API version, for example retired creation paths or targeting settings. Check the API deprecations page as well as release notes.

### What Not To Present As Fact
- Do not quote old code samples as if they prove current API behavior.
- Do not invent service names, fields, or method behavior from memory.
- Do not answer field-level compatibility questions from this topic alone; escalate to exact docs or tool metadata.

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
| [Google Ads API - Campaign](https://developers.google.com/google-ads/api/reference/rpc/v25/Campaign) | 2026-08-17 | 2026-10-09 |
| [Google Ads API - LiftMeasurementConfig](https://developers.google.com/google-ads/api/reference/rpc/v25/LiftMeasurementConfig) | 2026-08-17 | 2026-10-09 |
| [Google Ads API Docs - Campaigns](https://developers.google.com/google-ads/api/docs/campaigns/overview) | 2026-03-25 | 2026-04-03 |
| [Google Ads API Docs - Versioning](https://developers.google.com/google-ads/api/docs/concepts/versioning) | 2026-10-06 | 2026-10-09 |
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
| [Google Ads API Docs - Batch processing overview](https://developers.google.com/google-ads/api/docs/batch-processing/overview) | 2026-03-25 | 2026-04-03 |
