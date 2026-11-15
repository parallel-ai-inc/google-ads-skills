<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## GA4 ENGINEERING & TRUTH LAYER

### What Google-Owned Sources Support
- GA4 BigQuery export and the GA4 UI can differ because the UI can include reporting identities, thresholding, and modeled behavior that the export does not reproduce the same way.
- BigQuery export behavior can differ between streaming and daily export paths, especially for some attribution and new-user fields. Standard properties can export up to 1 million events a day, and streaming export is best-effort.
- Measurement Protocol requires the documented request identifiers, secrets, and payload structure; validate requests with Google’s debug tooling before assuming ingestion is correct.
- Measurement Protocol remains operational, but Google positions Data Manager API as future-proof infrastructure for server-to-server event integrations.
- Google has announced Meridian coming to Google Analytics 360 and QFCs eventually integrating with Meridian; keep that future-tense and do not state the integration is live until current Google-owned sources say so.

### Practical Truth-Layer Rules
1. Use GA4 UI for product-facing reporting behavior, but use the export when you need raw event analysis or warehouse joins.
2. Treat UI-vs-BigQuery mismatches as a modeling, identity, or export-path question before calling them a tracking failure.
3. When consent is limited, expect event completeness and identity stitching to change.
4. Keep the difference between reporting identity, export availability, and custom warehouse logic explicit in the answer.
5. Treat Data Manager map view, Data Manager API/tag-combination changes, Meridian Studio, and Meridian-in-GA360 updates as current Google-owned announcements with their stated rollout caveats. Meridian GeoX, announced at GML 2026 for testing later in the year, is now available as an open-source library (developers.google.com/meridian/geox).

### Measurement Protocol And Event Governance
- Follow the Measurement Protocol reference for required fields, limits, and validation.
- Use debug validation before trusting a new payload shape.
- Keep event names, parameters, and custom dimensions governed; do not solve measurement chaos by adding more ad hoc events.
- If the question depends on the latest export schema or MP behavior, corroborate with current developer docs before stating specifics.

### What Not To Present As Fact
- Do not call BigQuery the universal “truth” without naming the reporting, attribution, and consent caveats that still apply.
- Do not present one stitched identity rule as if it were guaranteed across UI, export, and every consent state.
- Do not promise that custom sessionization logic exactly reproduces GA4 UI numbers unless the implementation has been validated for that property.
- Do not claim Meridian in Google Analytics 360, QFC-to-Meridian integration, or Data Manager map view are generally available if the source says soon, eventually, or coming weeks/months.

### Companion Topics
- Signal wiring: the "Signal Injection & Tracking" reference
- Operating-model setup: the "Platform Ontology & Object Model" reference, the "Workflow Operations" reference
- Account-specific diagnosis: the "Reporting & Diagnostics" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Analytics Help - BigQuery Export](https://support.google.com/analytics/answer/9358801) | 2026-03-18 | 2026-10-14 |
| [Google Analytics Developers - Measurement Protocol reference](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference) | 2026-06-08 | 2026-06-20 |
| [Google Marketing Platform Blog - Google Analytics 360 helps you turn data into decisions](https://blog.google/products/marketingplatform/analytics/meridian-google-analytics-360/) | 2026-05-20 | 2026-10-14 |
| [Google for Developers - Set up consent mode on websites](https://developers.google.com/tag-platform/security/guides/consent) | 2026-10-13 | 2026-10-14 |
| [Google for Developers - Meridian GeoX](https://developers.google.com/meridian/geox) | 2026-10-14 | 2026-10-14 |
| [Google Ads & Commerce Blog - Turn your data into decisions: 3 things your business needs for growth in the AI era](https://blog.google/products/ads-commerce/google-marketing-live-2026-turn-your-data-into-decisions/) | 2026-05-05 | 2026-10-14 |
