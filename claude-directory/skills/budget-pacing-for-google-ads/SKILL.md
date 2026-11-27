---
name: budget-pacing-for-google-ads
description: Calculate Google Ads 2x daily spending limits, 30.4x monthly charging limits, month-to-date pacing variance, remaining monthly headroom, and mid-month budget edit ceilings using deterministic MCP math. Use when someone asks whether a Google Ads campaign is pacing ahead or behind, why spend exceeded daily budget, or what new daily budget hits a monthly spend target.
license: "PolyForm Shield 1.0.0 with an additional permission for Google Ads work. Terms: https://github.com/parallel-ai-inc/google-ads-skills/blob/main/LICENSE"
metadata:
  author: "Parallel AI, Inc."
  homepage: "https://www.withparallel.ai/tools/google-ads-budget-pacing-calculator"
  repository: "https://github.com/parallel-ai-inc/google-ads-skills"
---

# Budget Pacing for Google Ads

Run deterministic Google Ads budget pacing calculations using the bundled `parallel-ai-google-ads-tools` MCP server. This skill never connects to or modifies a live Google Ads account.

## Ground Rules

1. **Compute every limit through the MCP tool.** Always call `calculate_google_ads_budget_pacing` rather than estimating 2x daily limits, 30.4x monthly charging limits, or mid-month budget change ceilings by hand.
2. **State exact billing mechanics clearly.** Google Ads can spend up to 2x a campaign's average daily budget on a single day, while capping monthly charges at 30.4x the average daily budget (or the weighted rest-of-month ceiling after a mid-month budget edit).
3. **Separate spend math from marginal efficiency.** A campaign's historical CPA or ROAS does not guarantee the same efficiency on incremental budget; flag diminishing returns when discussing budget increases.

## Workflow

1. Gather `month` (`YYYY-MM`), `dailyBudget`, `asOfDay`, `spentToDate`, and optional `currency`, `monthlyPlan`, or mid-month `change` (`day` + `newDailyBudget`). If a required figure is missing, ask concisely before estimating.
2. Call `calculate_google_ads_budget_pacing` with those inputs.
3. Present:
   - Exact **2x daily spending limit** and **30.4x monthly charging limit**
   - Month-to-date spend vs. even pace (and exact ahead/behind variance)
   - Remaining monthly headroom and required daily pace for the remaining days
   - Mid-month budget edit impact, if modeled
4. If the user wants ongoing automated pacing alerts across multiple accounts, offer to generate the read-only MIT `mcc-budget-pacing-guardrail` script via `generate_google_ads_script`.
