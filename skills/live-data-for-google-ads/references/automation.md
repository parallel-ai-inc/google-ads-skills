<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## AUTOMATION STACK

### Official Automation Surfaces
- Product automation: Smart Bidding, Performance Max, and other Google-managed optimization systems.
- Workflow automation: batch processing, bulk edits, and version-aware API operations.
- Script automation: Google Ads Scripts with documented runtime and quota limits.
- Operator-built automation: warehouse jobs, alerting, or QA pipelines layered on top of official product surfaces.

### Durable Rules
- Scripts, API quotas, and system limits are real constraints. They should shape workflow design before you promise a large automation job will fit.
- Batch jobs and async mutation flows are the official path for large write workloads.
- Operator-built automation is not the same thing as platform behavior. Keep custom script logic labeled as operator-side implementation, not Google Ads platform fact.

### What The Agent Should Know
- When a user asks what is possible to automate officially, start with scripts, API workflows, batch jobs, and built-in product automation.
- When a user asks for a custom automation pattern, explain the official guardrails first, then label the custom pattern as implementation guidance.
- When the question is about current limits or quotas, corroborate with current developer docs before quoting a number.

### What Not To Present As Fact
- Do not present N-gram mining, anomaly thresholds, or custom budget-pacing logic as official Google Ads features.
- Do not promise that a script or API pattern is safe at any scale without checking the documented quotas and system limits.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-06-20.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - Set up automated rules](https://support.google.com/google-ads/answer/2472779) | 2026-06-11 | 2026-10-14 |
| [Google Ads Help - About Smart Bidding](https://support.google.com/google-ads/answer/7065882) | 2026-03-18 | 2026-10-14 |
| [Google Ads API Docs - Batch processing overview](https://developers.google.com/google-ads/api/docs/batch-processing/overview) | 2026-03-25 | 2026-04-03 |
| [Google Ads Scripts Docs - Limits](https://developers.google.com/google-ads/scripts/docs/limits) | 2025-12-03 | 2026-04-03 |
| [Google Ads API Docs - API limits and quotas](https://developers.google.com/google-ads/api/docs/best-practices/quotas) | 2026-03-26 | 2026-04-03 |
| [Google Ads API Docs - System limits](https://developers.google.com/google-ads/api/docs/best-practices/system-limits) | 2026-05-13 | 2026-10-14 |
| [Google Ads & Commerce Blog - Meet Ask Advisor, your new AI-powered collaborator](https://blog.google/products/ads-commerce/ask-advisor/) | 2026-05-20 | 2026-06-20 |
