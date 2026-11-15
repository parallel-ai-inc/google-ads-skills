<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## SCALING DYNAMICS

### Separate Platform Facts From Business Math
- Google documents planning and pacing surfaces such as Performance Planner, bid strategy reports, conversion delay estimates, and average daily budget delivery rules.
- Your own break-even mROAS, marginal CPA, and profit rules are business math. They may be useful, but they are not Google Ads platform thresholds.

### Official Planning Surfaces
- Performance Planner refreshes forecasts daily and simulates recent auctions using variables like seasonality, competitor activity, landing page, and conversion delay estimates.
- Most campaigns can spend up to 2x the average daily budget on a given day, with an average monthly cap of about 30.4x the daily budget.
- Bid strategy reports and average target metrics are official tools for judging whether a value-based strategy is tracking near its target before you tighten or loosen scale settings.

### Business Economics Layer
Use business formulas as operator-side decision tools, not as product rules:
```
mROAS_breakeven = 1 / Gross_Margin
mCPA = (Spend₂ - Spend₁) / (Conv₂ - Conv₁)
mROAS = (Revenue₂ - Revenue₁) / (Spend₂ - Spend₁)
```

### Safe Scaling Workflow
1. Validate measurement, primary conversions, and conversion delay before judging recent performance.
2. Use Performance Planner, bid strategy reports, simulators, and recent account evidence before changing scale settings.
3. Confirm the business can absorb more demand: inventory, sales capacity, margin, promos, and landing-page readiness.
4. Increase or loosen only when incremental economics and account health support it.
5. Re-check realized performance outside the most recent conversion-delay window before making another major move.

### What Not To Treat As Platform Rules
- There is no universal Google Ads rule that budgets must equal 3-5x tCPA.
- There is no universal platform rule that budget changes must always be limited to 20%.
- Impression share, planner eligibility, and campaign-type requirements are context-specific; confirm current product guidance before quoting numbers as fact.

### Research-Grade Measurement For Scale Decisions
- Use geo experiments or other causal measurement when the business question is true incremental return on ad spend, not just observed ROAS.
- Since August 17, 2026, budget-limited Target CPA and Target ROAS campaigns bid toward their stated target, so added budget scales at the target rather than at past overachievement; set the target you actually want before adding budget, and judge a budget increase after 1-2 conversion cycles.
- Observational media mix or blended ROAS reads can be biased, especially for paid search, so use experiments or bias-corrected methods for major scaling decisions.

### Expansion Ladders
- **Query expansion:** Exact/Phrase -> current Search expansion controls such as AI Max search term matching, broad match, and Smart Bidding when traffic quality and conversion semantics are stable. Treat DSA as a legacy/transition catch-all surface unless an existing DSA campaign explicitly needs review.
- **Bidding expansion:** Smart Bidding Exploration can be considered for eligible Search campaigns using Target ROAS; do not claim PMax or Shopping availability without current account/source corroboration.
- **Creative pipeline:** Concept -> Test -> Scale winners while refreshing assets as reach expands.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - About Performance Planner](https://support.google.com/google-ads/answer/9230124) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About spending limits](https://support.google.com/google-ads/answer/10486637) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - How AI Max for Search campaigns works](https://support.google.com/google-ads/answer/15910187?hl=en) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Smart Bidding Exploration](https://support.google.com/google-ads/answer/15489627?hl=en) | 2026-06-20 | 2026-10-14 |
| [Google Research - Measuring Ad Effectiveness Using Geo Experiments](https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/) | 2026-03-18 | 2026-10-14 |
| [Google Research - Bias Correction For Paid Search In Media Mix Modeling](https://research.google/pubs/bias-correction-for-paid-search-in-media-mix-modeling/) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Changes to target based bid strategies](https://support.google.com/google-ads/answer/17061251) | 2026-10-14 | 2026-10-14 |
| [Google Ads & Commerce Blog - We're upgrading Dynamic Search Ads to AI Max](https://blog.google/products/ads-commerce/dsa-upgrade-to-ai-max-2026/) | 2026-06-11 | 2026-10-14 |
| [Google Ads & Commerce Blog - New AI-powered bidding and budgeting innovations in Search and Shopping](https://blog.google/products/ads-commerce/bidding-budgeting-google-marketing-live-2026/) | 2026-05-07 | 2026-10-14 |
| [Google Research - A Field Guide for Pacing Budget and ROS Constraints](https://research.google/pubs/a-field-guide-for-pacing-budget-and-ros-constraints/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Optimal Mechanisms for Value Maximizers with Budget Constraints via Target Clipping](https://research.google/pubs/optimal-mechanisms-for-value-maximizers-with-budget-constraints-via-target-clipping/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Autobidding with Constraints](https://research.google/pubs/autobidding-with-constraints/) | 2026-06-20 | 2026-06-21 |
