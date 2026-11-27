---
name: demand-gen-2026-audit-for-google-ads
description: "Audit Google Ads Demand Gen campaigns against verified 2026 mechanics including silent OPTED_IN ad-level asset automation defaults, Video vs. Image channel isolation, SEARCH vs. AUTO custom segment dilution, optimized targeting, Secondary non-biddable early-funnel signals, and vertical-agnostic sample calibration. Use when auditing, troubleshooting, or launching Demand Gen campaigns."
license: "PolyForm Shield 1.0.0 with an additional permission for Google Ads work. Terms: https://github.com/parallel-ai-inc/google-ads-skills/blob/main/LICENSE"
metadata:
  author: "Parallel AI, Inc."
  homepage: "https://www.withparallel.ai/resources/google-ads-changes-tracker"
  repository: "https://github.com/parallel-ai-inc/google-ads-skills"
---

# 2026 Demand Gen Audit for Google Ads

Audit Demand Gen campaigns with official-source-verified 2026 Google Ads mechanics via the bundled `parallel-ai-google-ads-tools` MCP server.

## Ground Rules

1. **Separate verified 2026 Google Ads mechanics from vertical-specific judgment.** Never apply one vertical's pattern universally—mobile-first e-commerce, local services, lead gen, and B2B SaaS have different buyer economics and conversion lag.
2. **Always check silent creative automation defaults.** New Demand Gen multi-asset and video ads default generative automations (`GENERATE_VIDEOS_FROM_OTHER_ASSETS`, `GENERATE_DESIGN_VERSIONS_FOR_IMAGES`, `GENERATE_VERTICAL_YOUTUBE_VIDEOS`, `GENERATE_SHORTER_YOUTUBE_VIDEOS`, `GENERATE_LANDING_PAGE_TEXT`) to `OPTED_IN`.
3. **Never recommend native portfolio bid strategies for Demand Gen.** Demand Gen does not support native Google Ads portfolio bid strategies.

## Workflow

1. Call `lookup_google_ads_2026_mechanics` with `category: "demand-gen"` and `category: "bidding-signals"`, plus `lookup_google_ads_platform_changes` with `track: "demand-gen"`.
2. Walk through five core diagnostic checks calibrated to the advertiser's business model:
   - **Ad-level asset automation:** Check for unreviewed `OPTED_IN` generative variants and `(ad name) auto-generated video ad` spend leakage.
   - **Video vs. Image & Channel Controls:** Verify whether low-CPM Discover/image inventory is starving YouTube/Shorts/CTV ad groups.
   - **Custom segments & optimized targeting:** Distinguish explicit `SEARCH` intent custom segments from loose `AUTO` URL-browse expansions and confirm `optimized_targeting_enabled` is intentional.
   - **Conversion signal design:** Confirm Primary goals bid strictly on deep commercial outcomes while early-funnel events feed as Secondary actions in standard categories.
   - **Sample-size & lag discipline:** Verify conversion lag and sufficient spend/clicks before pausing devices, ages, or creatives.
3. If the user needs an API query to inspect Demand Gen ads or asset automation settings, validate it with `validate_google_ads_gaql_query`.
