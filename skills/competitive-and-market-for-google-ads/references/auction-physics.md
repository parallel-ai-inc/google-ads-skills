<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## AUCTION PHYSICS

### What Google Publicly Documents
Google Ads does not publish a single modern Search auction equation. Use auction language directionally, not as a substitute for live account evidence.

### Google Research Mechanism Layer
- Google Research frames sponsored search as an auction among advertisers where bidding and pricing algorithms use mechanism design, optimization, and statistical estimation.
- Google Research covers Generalized Second Price (GSP), VCG-related mechanism design, matching-market allocation, and bid multiplied by click-through-rate ranking as scientific models for sponsored search.
- Google Research also shows why simple formulas are incomplete: user behavior, assignment structure, pCTR calibration, dynamic reserves, black-box dynamic incentive testing, and incentive compatibility can change the efficient allocation and pricing story.
- Newer work models users' future clicks as responding to the quality of ads they see (so ad quality and personalized reserve-like thresholds matter beyond one auction), auctions that choose among rich formats such as images, sitelinks and video per advertiser (the theory behind Google's documented "expected impact of assets and other ad formats"), CTR models judged by auction welfare, and token auctions for ads inside generative AI output (a research direction, not a description of ads in AI Overviews or AI Mode).
- Treat this as first-principles auction intelligence for diagnosis and strategy, not as an exact current Google Ads production equation.

### Official Auction Inputs
- Ad Rank determines whether an ad is eligible to show and where it can appear.
- Ad Rank is influenced by bid, ad quality, Ad Rank thresholds, auction competitiveness, the user's search context, and the expected impact of assets and other ad formats.
- Ad Rank thresholds are dynamic at auction time. Higher positions carry higher thresholds, and lower-quality ads effectively need more bid support to clear them.

### What Not To Present As Fact
- Do not claim a current rGSP randomization band, squashing exponent, or exact reserve-price formula unless a current Google-owned source of the right claim family publishes it.
- Do not treat the 1-10 UI Quality Score as the same thing as auction-time Ad Rank.
- Do not reduce Smart Bidding to a published closed-form bid equation; Google documents auction-time optimization, not a canonical public formula.

### Operator Implications
- Diagnose rank loss with evidence: Search Lost IS (rank), top/abs. top metrics, auction insights, asset coverage, and landing page relevance.
- If CPC rises while impression share falls, check competitiveness, thresholds, asset impact, and landing-page quality before assuming bid caps are the only lever.
- Use auction concepts to explain directionally, then ground recommendations in account data instead of speculative auction internals.

### Economic Guardrail
Treat marginal economics as a business-layer heuristic:
```
mROAS_breakeven = 1 / gross_margin
```
Increase spend only while incremental value remains above business breakeven.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - About Ad Rank](https://support.google.com/google-ads/answer/1722122) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About Quality Score](https://support.google.com/google-ads/answer/6167118) | 2026-03-18 | 2026-10-14 |
| [Google Research - Algorithmic Methods for Sponsored Search Advertising](https://research.google/pubs/algorithmic-methods-for-sponsored-search-advertising/) | 2026-06-20 | 2026-06-21 |
| [Google Research - General Auction Mechanism for Search Advertising](https://research.google/pubs/general-auction-mechanism-for-search-advertising/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Sponsored Search Auctions for Markovian Users](https://research.google/pubs/sponsored-search-auctions-for-markovian-users/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Scale Calibration of Deep Ranking Models](https://research.google/pubs/scale-calibration-of-deep-ranking-models/) | 2026-06-20 | 2026-06-21 |
| [Google Research - A Data-Driven Metric of Incentive Compatibility](https://research.google/pubs/a-data-driven-metric-of-incentive-compatibility/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Testing Dynamic Incentive Compatibility in Display Ad Auctions](https://research.google/pubs/testing-dynamic-incentive-compatibility-in-display-ad-auctions/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Revenue-Incentive Tradeoffs in Dynamic Reserve Pricing](https://research.google/pubs/revenue-incentive-tradeoffs-in-dynamic-reserve-pricing/) | 2026-06-20 | 2026-06-21 |
| [Google Research - User Response in Ad Auctions: An MDP Formulation of Long-term Revenue Optimization](https://research.google/pubs/user-response-in-ad-auctions-an-mdp-formulation-of-long-term-revenue-optimization/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Simple Mechanisms for Welfare Maximization in Rich Advertising Auctions](https://research.google/pubs/simple-mechanisms-for-welfare-maximization-in-rich-advertising-auctions/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Pairwise Ranking Losses of Click-Through Rates Prediction for Welfare Maximization in Ad Auctions](https://research.google/pubs/pairwise-ranking-losses-of-click-through-rates-prediction-for-welfare-maximization-in-ad-auctions/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Bayesian Calibrated Click-Through Auctions](https://research.google/pubs/bayesian-calibrated-click-through-auctions/) | 2026-10-14 | 2026-10-14 |
| [Google Research Blog - Mechanism design for large language models](https://research.google/blog/mechanism-design-for-large-language-models/) | 2025-02-13 | 2026-10-14 |
