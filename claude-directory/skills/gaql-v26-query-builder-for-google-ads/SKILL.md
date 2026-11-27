---
name: gaql-v26-query-builder-for-google-ads
description: Build, lint, and validate Google Ads Query Language (GAQL) queries against the Google Ads API v26 field catalog and check 2026 Google Ads API v23–v26.2 breaking changes and sunsets. Use when writing or debugging GAQL queries for campaigns, search_term_view, asset_group, shopping_performance_view, or change_event.
license: "PolyForm Shield 1.0.0 with an additional permission for Google Ads work. Terms: https://github.com/parallel-ai-inc/google-ads-skills/blob/main/LICENSE"
metadata:
  author: "Parallel AI, Inc."
  homepage: "https://www.withparallel.ai/tools/gaql-query-builder"
  repository: "https://github.com/parallel-ai-inc/google-ads-skills"
---

# GAQL v26 Query Builder & Validator for Google Ads

Build and validate Google Ads API v26 GAQL queries deterministically using the bundled `parallel-ai-google-ads-tools` MCP server.

## Ground Rules

1. **Always validate GAQL through `validate_google_ads_gaql_query` before giving it to the user.** Do not guess field compatibility, segment rules, or operator syntax from memory.
2. **Check API version sunsets and schema changes** with `lookup_google_ads_platform_changes` (`track: "api"`) whenever migrating queries across Google Ads API v23–v26.2.

## Workflow

1. Accept either a draft raw GAQL string (`gaql`) or structured parameters (`resource`, `select`, `where`, `orderBy`, `limit`).
2. Call `validate_google_ads_gaql_query`.
3. If validation returns any errors or warnings, fix the query and re-validate until `valid: true`.
4. Return the validated GAQL query alongside any API v26 notes (for example, `metrics.cost_micros` unit conversion by dividing by `1,000,000` and date segment filters).
