---
name: ga4-conversion-debugging-for-google-ads
description: Reconcile discrepancies between Google Ads conversions and Google Analytics 4 (GA4) key events across click-time vs. event-time reporting, attribution models, counting settings, Consent Mode v2 modeling, auto-tagging, and conversion lag, plus verify 2026 conversion-goal bidding signal hygiene. Use when Google Ads and GA4 numbers disagree or conversions drop.
license: "PolyForm Shield 1.0.0 with an additional permission for Google Ads work. Terms: https://github.com/parallel-ai-inc/google-ads-skills/blob/main/LICENSE"
metadata:
  author: "Parallel AI, Inc."
  homepage: "https://www.withparallel.ai/tools/ga4-vs-google-ads-conversion-debugger"
  repository: "https://github.com/parallel-ai-inc/google-ads-skills"
---

# GA4 vs. Google Ads Conversion Debugging

Diagnose gaps between Google Ads conversions and GA4 key events deterministically using the bundled `parallel-ai-google-ads-tools` MCP server.

## Ground Rules

1. **Always reconcile structural reporting differences before blaming tags.** Click-date vs. conversion-date reporting, data-driven vs. cross-channel attribution, view-through or engaged-view inclusions, and Consent Mode modeling routinely create large expected gaps.
2. **Check conversion lag before judging recent days.** Never declare a tracking failure on the most recent 1–7 days without accounting for the account's median days-to-conversion.
3. **Separate Primary commercial outcomes from Secondary early-funnel signals.** Under count-based Maximize conversions, mixing cheap micro-events into Primary goals causes Smart Bidding to chase shallow clicks; in 2026, Search Journey Awareness and Demand Gen learn from properly categorized Secondary actions instead.

## Workflow

1. Gather the reporting date `range` (`start` and `end`), Google Ads `conversions`, GA4 `keyEvents`, and any known settings (`autoTagging`, `consentMode`, `medianLagDays`, counting mode, attribution model, import source).
2. Call `debug_ga4_vs_google_ads_conversions` to compute the gap direction and ranked root causes.
3. Call `lookup_google_ads_platform_changes` with `track: "measurement"` and `lookup_google_ads_2026_mechanics` with `category: "bidding-signals"` or `"measurement-diagnostics"` to ground recommendations in current 2026 rules.
4. Present the top causes ordered by impact with exact verification steps in Google Ads and GA4.
5. If the user wants automated daily alerts when conversions drop or landing pages break (404/5xx), offer the read-only MIT `conversion-drop-watchdog` script via `generate_google_ads_script`.
