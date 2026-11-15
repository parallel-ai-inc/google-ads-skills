<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## INCREMENTALITY TESTING

### Durable Measurement Distinctions
- Platform reporting is not the same thing as attribution.
- Attribution is not the same thing as incrementality.
- Incrementality is the causal question: what happened because ads ran, compared with what would have happened otherwise.

### Google-Owned Sources Support
- Google Research-backed geo experiments for causal measurement.
- Official lift-study surfaces such as Brand Lift where Google exposes them.
- Strong caution that observational performance alone can mislead major budget decisions, especially in search-heavy media mixes.
- Google Ads Help now frames incrementality, MMM, and attribution as complementary but distinct: incrementality answers causal impact, MMM gives a holistic media view, and attribution assigns touchpoint credit.
- Google lowered the entry cost of Google Ads incrementality experiments from as much as $100,000 to $5,000 (November 2025); access and eligibility still need live account checks.

### Google Ads Lift Studies
- Lift types: Brand Lift (Video, audio and Demand Gen), Search Lift, and Conversion Lift based on users or on geography. Geo-based Conversion Lift supports offline conversions but is noisier, has no demographic slices and needs higher budgets. Conversion Lift isn't available for all accounts and goes through a Google account representative.
- User-based Conversion Lift needs at least 1,000 observed conversions, a $5,000 minimum campaign budget and a compatible conversion action, and runs at least 7 days (14 recommended, longer with long conversion lags).
- Conversion Lift is moving to Bayesian methodology: priors from past studies, 80% credible intervals and a "certainty of lift"; results show once certainty exceeds 50% with at least 150 treatment and 65 control conversions and $5,000 spend. Rollout timing varies by account.
- Brand Lift budgets are set per 10 days by question count and country group; Enhanced Lift needs 3x the minimum.

### Geo Experiments
- Google's geo experiment guidance uses holdback, go-dark and heavy-up designs: target only test or control geos with the Presence location option and keep at least 3x the test length in pre-test data.
- Budgets in geo tests: holdback and capped go-dark campaigns get their own individual budgets. Shared budgets and portfolio bidding are recommended for capped-budget campaigns only inside one cell, never across cells and never in go-dark tests; a Smart Bidding heavy-up arm should use a shared budget.
- Learning in geo tests: duplicating a campaign starts a learning period, so duplicate early and remove that period from the final analysis; only the typical 4-5 day heavy-up learning period must fall inside the test period. The page also says budget changes over 20% start a new learning period (geo-test guidance, not the bid strategy status rule).
- Meridian GeoX is Google's open-source, publisher-agnostic geo experiment library, now available globally; its results can become priors for Meridian.

### MMM (Meridian)
- Meridian is Google's open-source Bayesian marketing mix model (generally available since January 2025): it models lagged effects and saturation, uses Google Query Volume to control for organic demand, can use reach and frequency and geo-level data, takes incrementality results as priors, and supports budget optimization; Scenario Planner (February 2026) is a no-code interface for budget scenarios. It is an analyst-side model, not a Google Ads report.

### Google Research Methods (Theory)
- Geo tests: time-based regression for few geos or matched markets, Trimmed Match for robust iROAS from paired geos (budget constraints create interference between geos), Trimmed Match Design for few heavy-tailed geos, continuous geo experiments that rotate assignment, and CausalImpact when no randomized holdout exists.
- MMM: advertising has lag and diminishing returns, geo-level data tightens intervals, and priors set from experiment ROAS reduce bias; Google Research also documents why MMMs struggle to give consistently valid answers.
- A 2012 Google meta-analysis of Search Ads Pause studies found ad clicks less incremental when the advertiser already ranked first organically. Historical averages, not a current rate; test brand incrementality with an experiment.

### Safe Operating Model
1. Use attribution to understand credit assignment and reporting behavior.
2. Use planner or standard reporting for operational forecasts and diagnostics.
3. Use experiments or causal measurement when the user is asking whether spend is truly incremental.
4. Use Google Research methodology to reason about design quality, selection bias, and geo-test interpretation before turning platform metrics into business-causality claims.

### What Not To Present As Fact
- Do not collapse attribution and incrementality into one metric.
- Do not present a single experiment design as the only correct method for every campaign type or business size.
- Do not restate old ghost-ad, variance-reduction, or lift-threshold mechanics as Google Ads product rules unless a current Google-owned source supports the exact claim. Google now publishes exact Conversion Lift thresholds (see the claims); cite those rather than older third-party mechanics.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - LiftMeasurementConfig](https://developers.google.com/google-ads/api/reference/rpc/v25/LiftMeasurementConfig) | 2026-08-17 | 2026-10-09 |
| [Google Research - Measuring Ad Effectiveness Using Geo Experiments](https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/) | 2026-03-18 | 2026-10-14 |
| [Google Research - Bias Correction For Paid Search In Media Mix Modeling](https://research.google/pubs/bias-correction-for-paid-search-in-media-mix-modeling/) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Set up Brand Lift](https://support.google.com/google-ads/answer/9049373) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Strengthen media measurement and ROI clarity with incrementality testing improvements](https://support.google.com/google-ads/answer/16719772) | 2025-11-11 | 2026-10-14 |
| [Google Ads Help - Comparing lift types](https://support.google.com/google-ads/answer/14097991) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Conversion Lift](https://support.google.com/google-ads/answer/12003020) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Set up Conversion Lift based on users](https://support.google.com/google-ads/answer/12005564) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Bayesian methodology in Conversion Lift](https://support.google.com/google-ads/answer/16627074) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Implement campaigns for geo experiments](https://support.google.com/google-ads/answer/18073432) | 2026-10-14 | 2026-10-14 |
| [Google for Developers - An introduction to Meridian](https://developers.google.com/meridian/docs/basics/meridian-introduction) | 2026-07-09 | 2026-10-14 |
| [Google for Developers - Meridian GeoX](https://developers.google.com/meridian/geox) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About attribution models](https://support.google.com/google-ads/answer/6259715) | 2026-03-18 | 2026-10-14 |
| [Google Ads & Commerce Blog - Meridian is now available to everyone](https://blog.google/products/ads-commerce/meridian-marketing-mix-model-open-to-everyone/) | 2025-01-29 | 2026-10-14 |
| [Google Ads & Commerce Blog - New Meridian tool puts MMM insights directly in marketers' hands](https://blog.google/products/ads-commerce/new-meridian-tool-puts-mmm-insights-directly-in-marketers-hands/) | 2026-02-19 | 2026-10-14 |
| [Google Research - Estimating Ad Effectiveness using Geo Experiments in a Time-Based Regression Framework](https://research.google/pubs/estimating-ad-effectiveness-using-geo-experiments-in-a-time-based-regression-framework/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Robust Causal Inference for Incremental Return on Ad Spend with Randomized Paired Geo Experiments](https://research.google/pubs/robust-causal-inference-for-incremental-return-on-ad-spend-with-randomized-paired-geo-experiments/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Trimmed Match Design for Randomized Paired Geo Experiments](https://research.google/pubs/trimmed-match-design-for-randomized-paired-geo-experiments/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Inferring causal impact using Bayesian structural time-series models](https://research.google/pubs/inferring-causal-impact-using-bayesian-structural-time-series-models/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Bayesian Methods for Media Mix Modeling with Carryover and Shape Effects](https://research.google/pubs/bayesian-methods-for-media-mix-modeling-with-carryover-and-shape-effects/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Geo-level Bayesian Hierarchical Media Mix Modeling](https://research.google/pubs/geo-level-bayesian-hierarchical-media-mix-modeling/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Bayesian Hierarchical Media Mix Model Incorporating Reach and Frequency Data](https://research.google/pubs/bayesian-hierarchical-media-mix-model-incorporating-reach-and-frequency-data/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Media Mix Model Calibration With Bayesian Priors](https://research.google/pubs/media-mix-model-calibration-with-bayesian-priors/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Challenges and Opportunities in Media Mix Modeling](https://research.google/pubs/challenges-and-opportunities-in-media-mix-modeling/) | 2026-10-14 | 2026-10-14 |
| [Google Research Blog - Impact of Organic Ranking on Ad Click Incrementality](https://research.google/blog/impact-of-organic-ranking-on-ad-click-incrementality/) | 2012-03-27 | 2026-10-14 |
| [Google Research Blog - Running Continuous Geo Experiments to Assess Ad Effectiveness](https://research.google/blog/running-continuous-geo-experiments-to-assess-ad-effectiveness/) | 2012-09-18 | 2026-10-14 |
