---
name: read-only-scripts-for-google-ads
description: Configure and generate ready-to-paste, read-only MIT-licensed Google Ads Scripts (AdsApp.search only; zero account mutations) for PMax placement bleed, MCC 30.4x budget pacing, zero-conversion search term audits, Shopping zombie SKUs, and landing-page 404 / conversion-drop watchdogs. Use when a user wants an automated Google Ads Script to export diagnostics to Google Sheets or email.
license: "PolyForm Shield 1.0.0 with an additional permission for Google Ads work. Terms: https://github.com/parallel-ai-inc/google-ads-skills/blob/main/LICENSE"
metadata:
  author: "Parallel AI, Inc."
  homepage: "https://www.withparallel.ai/scripts"
  repository: "https://github.com/parallel-ai-inc/google-ads-skills"
---

# Read-Only MIT Google Ads Scripts

Generate validated, copy-paste, read-only MIT Google Ads Scripts using the bundled `parallel-ai-google-ads-tools` MCP server. Every generated script uses `AdsApp.search` for reads and writes only to Google Sheets or alert emails (`mutatesGoogleAds: false`).

## Ground Rules

1. **Always render scripts through `generate_google_ads_script`** rather than writing Google Ads Scripts from scratch by hand.
2. **Keep personal or private config fields blank by default** (such as `sheetUrl` or `emailTo`) unless the user explicitly provides values to embed in `CONFIG`.
3. **State exact scope (`ACCOUNT` vs. `MANAGER`) and suggested schedule (`DAILY` / `WEEKLY`)** with every script.

## Workflow

1. If the user has not chosen a specific script, call `generate_google_ads_script` with no arguments to list all 5 read-only MIT scripts and their configurable fields:
   - `pmax-placement-bleed-monitor`
   - `mcc-budget-pacing-guardrail`
   - `wasted-spend-search-term-auditor`
   - `shopping-zombie-sku-detector`
   - `conversion-drop-watchdog`
2. Call `generate_google_ads_script` with the chosen `slug` and any user-requested `config` overrides.
3. Deliver the rendered JavaScript, confirm `mutatesGoogleAds: false`, and note where to paste it inside Google Ads (**Tools -> Bulk Actions -> Scripts**) and how often to schedule it.
