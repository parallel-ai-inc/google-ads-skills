<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## AD SPECS & PLATFORM LIMITS

### What This Topic Covers
- Current asset requirements from the Google Ads specs guide
- Account and entity limits from current Help Center and developer docs
- System limits that matter when building or automating at scale

### Durable Rules
- Asset requirements vary by campaign type. Search, Demand Gen, App, Display, Video, and Performance Max do not share one universal asset template.
- Specs and limits are release-sensitive. If the user asks for the current exact limit, use the official Google-owned source or current web corroboration rather than memory.
- Account limits and system limits constrain what can be created or automated, but they do not tell you whether a given strategy is a good idea.

### Common Current Examples
- Search text assets still use short headline and description limits rather than long-form social-style copy.
- Demand Gen, App, Display, and Performance Max all require campaign-type-specific image or video ratios and counts.
- Business name, logo, final URL, and current asset-quantity requirements can differ by campaign type.
- Current official limits include examples such as 3 enabled responsive search ads per ad group, 100 Performance Max campaigns per account, 50 labels per entity, and 1,000 listing group filters per asset group.
- Account-level limits and API system limits can block large-scale buildouts even when the UI setup looks conceptually valid.

### Safe Usage Pattern
1. Identify the campaign type first.
2. Use the specs guide for the current asset requirements for that family.
3. Use account and system limits only when the user is asking about scale, automation, or why something cannot be created.

### What Not To Present As Fact
- Do not quote stale asset counts, file sizes, or campaign-type requirements from old memory.
- Do not treat historical HTML5 or media-upload rules as current unless the current specs or Help Center still say so.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - Google Ads specs: ad formats, sizes, and best practices](https://support.google.com/google-ads/answer/13676244) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About your Google Ads account limits](https://support.google.com/google-ads/answer/6372658) | 2026-03-18 | 2026-10-14 |
| [Google Ads API Docs - System limits](https://developers.google.com/google-ads/api/docs/best-practices/system-limits) | 2026-05-13 | 2026-10-14 |
