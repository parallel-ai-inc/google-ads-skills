# Parallel AI for Google Ads (Claude Plugin)

Zero-OAuth, read-only Google Ads analysis tools and operator workflows from **Parallel AI** ([withparallel.ai](https://www.withparallel.ai)), powered by our stateless Streamable HTTP MCP server at `https://www.withparallel.ai/api/mcp`.

Works across Claude.ai (web, desktop, mobile), Cowork, and Claude Code without Google Ads OAuth credentials, API keys, or local Python setup. None of these tools connect to, read from, or modify live Google Ads accounts—every calculation runs deterministically on the figures or CSV exports you share in conversation.

## Included MCP Tools (`parallel-ai-google-ads-tools`)

1. `calculate_google_ads_budget_pacing` — Exact 2x daily spending limits, 30.4x monthly charging limits, month-to-date variance, remaining headroom, and mid-month budget change ceilings.
2. `audit_google_ads_search_terms_csv` — Deterministic Search Terms CSV/TSV auditor for zero-conversion waste, high-CPA outliers, brand vs. non-brand mix, and 1-gram/2-gram negative keyword candidates.
3. `check_google_ads_negative_collisions` — Tests proposed negatives against active keywords and converting queries under Google Ads' exact negative matching rules (no close-variant matching).
4. `debug_ga4_vs_google_ads_conversions` — Reconciles GA4 key events against Google Ads conversions across click-time vs. event-time attribution, Consent Mode, auto-tagging, and conversion lag.
5. `estimate_pmax_waste_and_lead_quality` — Grades Performance Max placement and search-term exports for mobile-app games, parked domains, off-language traffic, and low-intent queries.
6. `validate_google_ads_gaql_query` — Builds, lints, and validates Google Ads Query Language (GAQL) queries against the Google Ads API v26 field catalog.
7. `lookup_google_ads_platform_changes` — Searches Parallel AI's official-source-cited 2026 Google Ads platform and API v23–v26.2 changes tracker.
8. `lookup_google_ads_2026_mechanics` — Official-source-verified 2026 Google Ads mechanics (Search Journey Awareness Secondary signals, Demand Gen silent asset automation defaults, PMax 2026 controls, portfolio bidding limits, and custom segments).
9. `generate_google_ads_script` — Generates ready-to-paste, read-only MIT-licensed Google Ads Scripts (`AdsApp.search` only; never mutates Google Ads).

## Included Skills

- `budget-pacing-for-google-ads`
- `search-terms-and-negatives-for-google-ads`
- `ga4-conversion-debugging-for-google-ads`
- `pmax-waste-triage-for-google-ads`
- `demand-gen-2026-audit-for-google-ads`
- `gaql-v26-query-builder-for-google-ads`
- `read-only-scripts-for-google-ads`

## Privacy & Scope

- **Read-only & Zero-OAuth:** No Google account sign-in, OAuth tokens, or live Google Ads account mutations.
- **Privacy Policy:** https://www.withparallel.ai/privacy-policy
- **Terms of Use:** https://www.withparallel.ai/terms-of-use
- **Support:** https://www.withparallel.ai/contact
