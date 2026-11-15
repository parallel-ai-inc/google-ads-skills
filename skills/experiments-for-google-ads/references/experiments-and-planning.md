<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## EXPERIMENTS & PLANNING

### Durable Planning Surfaces
- Performance Planner for forecast and scenario planning
- Official experiment surfaces where Google exposes them
- Lift studies such as Brand Lift
- Research-backed causal measurement methods such as geo experiments
- Conversion Lift (user and geo), Search Lift, geo experiments and Meridian: see the "Incrementality Testing" reference

### Custom Experiments
- Custom experiments run on Search, Display, Demand Gen and Video campaigns whose base campaign is active, on its own daily budget and on a standard (not portfolio) bid strategy; App and Shopping campaigns can't use them.
- A 50/50 split sets auction eligibility, not equal impressions or spend. Allow 7-14 days for the trial arm to settle, and turn off Experiment sync if trial-arm edits must not be overwritten. Experiment copies count toward account limits.
- Since API v24.1 Google reports per-arm results with a control average, the treatment-minus-control difference, a margin of error and a p-value; read significance from those rather than recomputing it from campaign totals.
- Performance Planner may propose a $0 budget and pausing, and applying its suggested changes edits live campaigns immediately; campaigns that changed bid strategy in the last 10 days or sit in an experiment can't be planned.

### Current Google-Owned Source Boundaries
- Performance Planner forecasts refresh daily, use recent auction simulations, and are scenario-planning guidance, not causal lift proof.
- Since March 9, 2026, Performance Planner no longer supports Display or Video campaigns, or plans whose primary metric is based on impression share.
- Performance Planner can apply suggested changes directly into live campaigns, so planning-to-implementation advice must preserve mutation and approval caution.
- Performance Max experiment Help currently documents control/treatment campaign comparisons and eligibility-sensitive setup; do not assume every campaign is eligible.
- Google Ads API v24.1 added experiment types such as `ADOPT_AI_MAX`, `ADOPT_BROAD_MATCH_KEYWORDS`, `OPTIMIZE_ASSETS`, and `PMAX_REPLACEMENT_SHOPPING`, plus experiment-arm metric families. v24.2 added `COMPARE_CAMPAIGNS` and `PMAX_TEXT_CUSTOMIZATION_FINAL_URL_EXPANSION`; these are also present in v25. API enum support is not live-account eligibility.
- Intra-campaign experiments for `ADOPT_AI_MAX` and `ADOPT_BROAD_MATCH_KEYWORDS` split traffic inside one campaign rather than between separate control and treatment campaigns.

### Operating Model
- Planning estimates, attribution reports, and true incrementality are different things.
- Use planner outputs to size scenarios and operational tradeoffs.
- Use experiments or causal measurement to answer whether spend is incrementally working.
- Use attribution to understand credit assignment, not to prove lift by itself.

### Normal Operations
- Build a planning scenario from current campaign structure and constraints.
- Decide whether the next question is forecast, optimization, or causal validation.
- Use the official experiment surface where available; use research-backed causal methods where the platform surface is insufficient.

### What Not To Present As Fact
- Do not treat modeled attribution as incrementality.
- Do not promise every account or campaign type has access to every lift-study or experiment surface.
- Do not treat Brand Lift availability, Enhanced Lift, custom experiment support, or API experiment fields as proof that the selected live account is eligible.
- Do not turn one experiment framework into a universal playbook for every business size or campaign type.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - LiftMeasurementConfig](https://developers.google.com/google-ads/api/reference/rpc/v25/LiftMeasurementConfig) | 2026-08-17 | 2026-10-09 |
| [Google Ads Help - About Performance Planner](https://support.google.com/google-ads/answer/9230124) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Set up Dynamic Search Ads or Google Display Ads campaign vs. Performance Max experiments](https://support.google.com/google-ads/answer/15637732) | 2026-03-18 | 2026-06-21 |
| [Google Ads Help - Set up Brand Lift](https://support.google.com/google-ads/answer/9049373) | 2026-03-18 | 2026-10-14 |
| [Google Ads API Docs - Intra-campaign experiments](https://developers.google.com/google-ads/api/docs/experiments/intra-campaign) | 2026-06-21 | 2026-06-21 |
| [Google Ads API Docs - Release notes](https://developers.google.com/google-ads/api/docs/release-notes) | 2026-09-30 | 2026-10-09 |
| [Google Research - Measuring Ad Effectiveness Using Geo Experiments](https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About custom experiments](https://support.google.com/google-ads/answer/10683687) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Strengthen media measurement and ROI clarity with incrementality testing improvements](https://support.google.com/google-ads/answer/16719772) | 2025-11-11 | 2026-10-14 |
| [Google Research - Bias Correction For Paid Search In Media Mix Modeling](https://research.google/pubs/bias-correction-for-paid-search-in-media-mix-modeling/) | 2026-03-18 | 2026-10-14 |
| [Google Ads Developer Blog - Announcing expanded experiment functionality in Google Ads API v24.1](https://ads-developers.googleblog.com/2026/05/announcing-expanded-experiment.html) | 2026-05-14 | 2026-10-14 |
