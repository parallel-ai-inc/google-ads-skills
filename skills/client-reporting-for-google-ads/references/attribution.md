<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## ATTRIBUTION MODELING

### Current Google Ads State
- Last click and data-driven attribution are the current Google Ads attribution models.
- First click, linear, time decay, and position-based models were retired and upgraded to data-driven attribution.
- Data-driven attribution is the default attribution model for most conversion actions.
- All conversion actions are eligible for data-driven attribution regardless of conversion or interaction volume, but Google recommends about 200 conversions and 2,000 ad interactions in supported networks within 30 days for stronger precision.

### What Official Sources Support
- Attribution model settings affect the Conversions and All conversions columns, and they affect automated bid strategies that use the Conversions column.
- Model changes are forward-looking in standard conversion columns, so use model comparison and current-model columns before assuming a performance shift is real.
- Switching to a non-last-click model can introduce fractional conversion credit, longer reporting lag for recent days, and credit shifts across campaigns, networks, ad groups, and keywords.
- Attribution reports can use 30-, 60-, or 90-day lookback windows, and those report lookbacks are different from conversion windows.
- Attribution reports process only conversions from the last 7 days and exclude Search partners, Gmail and App campaigns; offline conversions uploaded later still count in the standard columns and for Smart Bidding.
- Data-driven attribution assigns credit by comparing the paths of customers who convert with those who don't, across clicks and video engagements on Search (including Shopping), YouTube, Display and Demand Gen.
- If the question depends on current methodology detail, prefer Google Ads Help, developers.google.com, or Google Research over third-party explainers.

### What Primary Research Adds
- Google Research treats causal measurement and attribution as related but separate problems: credit assignment can help reporting, while geo experiments or other causal designs answer incrementality questions more directly.
- Google Research (2016) argues that common attribution models assume ads work only by changing conversion propensity along the path, so they can miss incremental conversions. That is theory, not a description of Google Ads data-driven attribution, and a reason to check attribution against experiments.
- Research-backed causal methods are especially useful when you need to know whether ad spend created incremental outcomes rather than how Google Ads distributed credit across a path.

### What Not To Claim
- Do not present Shapley values, Monte Carlo sampling, fixed upstream credit shifts, or exact lift percentages as current Google Ads platform facts unless a live methodology source explicitly states them.
- Do not interpret an attribution-model change before ruling out measurement breaks, conversion-action changes, or reporting windows.

### Operator Workflow
- Compare last click vs data-driven using CPA, conv. value/cost, and path role before changing bids.
- When moving from last click to DDA, expect credit to redistribute across the path, then validate against business outcomes or experiments.
- When evaluating a model change, wait until the average days to conversion has passed and exclude the most recent lagged period before recalibrating Target CPA or Target ROAS; Google's method is to take the percentage change between the current-model and previous columns and apply it to the target.
- Keep attribution discussion separate from incrementality: DDA allocates credit; it does not prove causal lift on its own.

### Companion Topics
- Tracking and upload health: the "Signal Injection & Tracking" reference
- Incrementality and lift: the "Incrementality Testing" reference, the "Experiments & Planning" reference
- Account diagnosis: the "Reporting & Diagnostics" reference

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - About attribution models](https://support.google.com/google-ads/answer/6259715) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Best practices for managing attribution model changes](https://support.google.com/google-ads/answer/9203352) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - About attribution reports](https://support.google.com/google-ads/answer/1722023) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - About data-driven attribution](https://support.google.com/google-ads/answer/6394265) | 2026-03-18 | 2026-10-14 |
| [Google Research - Measuring Ad Effectiveness Using Geo Experiments](https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/) | 2026-03-18 | 2026-10-14 |
| [Google Research - Toward Improving Digital Attribution Model Accuracy](https://research.google/pubs/toward-improving-digital-attribution-model-accuracy/) | 2026-10-14 | 2026-10-14 |
