<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## SMART BIDDING ARCHITECTURE

### What Google Currently Documents
- Smart Bidding uses Google AI to optimize for conversions or conversion value.
- It performs auction-time bidding, meaning bids are set at each auction instead of by a static list of rules.
- Google documents the use of query-level conversion data and contextual signals such as device, location, time of day, language, browser, operating system, and remarketing status, plus statistically significant signal combinations.
- Google's full signal list also includes location intent, ad characteristics, the actual search query, Search partner site, Display placement and site behavior, and Shopping product attributes, price competitiveness and seasonality.
- How it learns (Google's Smart Bidding guide): query-level data seeds conversion-rate models when data is thin, Bayesian learning refines them, and recent data is weighted more except where long conversion cycles delay conversions.

### Current Strategy Framing
| Strategy Family | Current Framing | Readiness Guidance |
|-----------------|-----------------|-------------------|
| Maximize conversions | Conversion volume first, optional target CPA in Search | Good entry point when you want the system to gather more signal |
| Maximize conversion value | Value volume first, optional target ROAS in Search | Requires reliable conversion values |
| Target CPA / Target ROAS | Constraints layered onto automated bidding outcomes | Works best when measurement is stable and recent data volume is usable |

Since June 2026 the Google Ads interface labels these as standalone Target CPA and Target ROAS strategies with the same bidding behavior; in the API, standard Search Target CPA is still set as Maximize conversions with a target.

### Google Research Autobidding Layer
- Google Research treats autobidding as a major online-advertising pattern and studies bidding algorithms, equilibrium/efficiency, and auction design under automated strategies.
- Constraint-based autobidding research models budget, value, cost, and return-on-spend targets as real constraints, not as one isolated bid knob.
- Research on pacing, joint budget/ROS optimization, target clipping, and value maximizers explains why aggressive targets, constrained budgets, poor value signals, and thin conversion data can create delivery or efficiency tradeoffs.
- Newer research: scaling every bid by one multiplier is optimal only in truthful auctions such as VCG and may not be in the generalized second-price and first-price formats ad platforms run in practice, pacing prices budget as a self-correcting opportunity cost, and interacting return-on-spend autobidders can oscillate with no account change.
- Use this layer to reason about why Smart Bidding may starve, pace, explore, or react to value-quality changes; do not present any research formula as the literal Google Ads tCPA or tROAS bid equation.

### Current Guardrails
- Target ROAS: most campaign types need at least 15 conversions in the past 30 days, with stricter requirements for some campaign types.
- After starting or changing Search value reporting, wait 1-2 conversion cycles before adopting Target ROAS; before value-based bidding, report values 3-4 weeks or 1-2 cycles, whichever is longer (Google's pages differ on 3 vs 4 weeks).
- Evaluate over periods with at least 30 conversions (50 for Target ROAS), against the average target, outside the conversion-delay window.
- On Search and Shopping, a target change moves bids immediately and doesn't start Learning; give it 1-2 conversion cycles, and expect a large change to move spend or volume by a similar amount. Same 1-2 cycles after a budget increase. Google's Demand Gen guide asks for smaller, slower bid changes (see the "Demand Gen Setup" reference).
- Since August 17, 2026, Target CPA and Target ROAS campaigns (and Target CPC on Demand Gen) Limited by budget bid toward their target rather than beating it (not App, Video reach or Video view); Google doesn't change targets or budgets for you, so set the target you actually want.
- Maximize conversions and Maximize conversion value are "limited by budget" by design; judge headroom with the budget simulator, not Lost IS (budget).

### Smart Bidding Exploration
- Google Help currently frames Smart Bidding Exploration as an opt-in feature available only for Search campaigns using Target ROAS.
- It uses flexible ROAS targets to capture additional conversions from traffic the campaign is already eligible for.
- It does not expand broad match keyword reach by itself; it works across existing eligible targeting such as broad match, Dynamic Search Ads, and AI Max.
- Google-owned blog language describes Performance Max and Shopping expansion as beta or coming-soon rollout context, not as universal current availability.

### Operator Guidance
- Treat Smart Bidding as a measurement system first: broken primary conversions or noisy values will train the wrong objective.
- Use bid strategy reports, simulators, conversion delay, and business guardrails before making major target changes.
- Avoid exact claims about hidden signal counts or pooling math unless a live Google source explicitly states them.

### Important Platform Change
Enhanced CPC is no longer available for Search and Display campaigns as of March 31, 2025. Legacy campaigns effectively use Manual CPC unless moved to a different bid strategy. Shopping also ignores enhanced CPC. Hotel has separate documented enhanced-CPC support on manual CPC and percent CPC. For Search, standard target CPA uses Maximize Conversions with a target, and standard target ROAS uses Maximize Conversion Value with a target. Do not apply those Search mappings universally: Hotel supports direct target ROAS, and Demand Gen examples use direct target CPA.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads API - Bidding strategy types](https://developers.google.com/google-ads/api/docs/campaigns/bidding/strategy-types) | 2026-09-30 | 2026-10-09 |
| [Google Ads API - Assign or update a Hotel bidding strategy](https://developers.google.com/google-ads/api/docs/hotel-ads/bidding/assign-strategies) | 2026-10-06 | 2026-10-09 |
| [Google Ads Help - About Smart Bidding](https://support.google.com/google-ads/answer/7065882) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About target ROAS bidding](https://support.google.com/google-ads/answer/6268637) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Enhanced CPC](https://support.google.com/google-ads/answer/2464964) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About Smart Bidding Exploration](https://support.google.com/google-ads/answer/15489627?hl=en) | 2026-06-20 | 2026-10-14 |
| [Google Ads Help - Changes to target based bid strategies](https://support.google.com/google-ads/answer/17061251) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Frequently asked questions about changes to Target-based bid strategies](https://support.google.com/google-ads/answer/17125145) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Maximize conversions bidding](https://support.google.com/google-ads/answer/7381968) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - How our bidding algorithms learn](https://support.google.com/google-ads/answer/10970825) | 2026-10-14 | 2026-10-15 |
| [Google Ads Help - How Google Ads calculates bids](https://support.google.com/google-ads/answer/10966879) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Evaluate your automated bid strategy's performance](https://support.google.com/google-ads/answer/10167267) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Target CPA bidding](https://support.google.com/google-ads/answer/6268632) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Maximize conversion value bidding](https://support.google.com/google-ads/answer/7684216) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Smart Bidding using value-based bidding for Search and Shopping](https://support.google.com/google-ads/answer/15099424) | 2026-10-14 | 2026-10-14 |
| [Google Ads & Commerce Blog - Smart Bidding Exploration](https://blog.google/products/ads-commerce/smart-bidding-exploration-ai/) | 2026-03-18 | 2026-06-20 |
| [Google Ads & Commerce Blog - New AI-powered bidding and budgeting innovations in Search and Shopping](https://blog.google/products/ads-commerce/bidding-budgeting-google-marketing-live-2026/) | 2026-05-07 | 2026-10-14 |
| [Google Research - Auto-bidding and Auctions in Online Advertising: A Survey](https://research.google/pubs/auto-bidding-and-auctions-in-online-advertising-a-survey/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Autobidding with Constraints](https://research.google/pubs/autobidding-with-constraints/) | 2026-06-20 | 2026-06-21 |
| [Google Research - A Field Guide for Pacing Budget and ROS Constraints](https://research.google/pubs/a-field-guide-for-pacing-budget-and-ros-constraints/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Optimal Mechanisms for Value Maximizers with Budget Constraints via Target Clipping](https://research.google/pubs/optimal-mechanisms-for-value-maximizers-with-budget-constraints-via-target-clipping/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Towards Efficient Auctions in an Auto-bidding World](https://research.google/pubs/towards-efficient-auctions-in-an-auto-bidding-world/) | 2026-06-20 | 2026-06-21 |
| [Google Research - Individual Welfare Guarantees in the Autobidding World with Machine-learned Advice](https://research.google/pubs/individual-welfare-guarantees-in-the-autobidding-world-with-machine-learned-advice/) | 2026-06-20 | 2026-06-21 |
| [Google Ads Help - Changes to how Smart Bidding strategies are organized for Search campaigns](https://support.google.com/google-ads/answer/10353027) | 2026-10-14 | 2026-10-14 |
| [Google Ads Developer Blog - Updates to Smart Bidding Strategy Naming](https://ads-developers.googleblog.com/2026/06/updates-to-smart-bidding-strategy.html) | 2026-06-16 | 2026-10-14 |
| [Google Research - Non-uniform Bid-scaling and Equilibria for Different Auctions: An Empirical Study](https://research.google/pubs/non-uniform-bid-scaling-and-equilibria-for-different-auctions-an-empirical-study/) | 2026-10-14 | 2026-10-14 |
| [Google Research Blog - Robust Online Allocation with Dual Mirror Descent](https://research.google/blog/robust-online-allocation-with-dual-mirror-descent/) | 2022-09-16 | 2026-10-14 |
| [Google Research - Complex Dynamics in Autobidding Systems](https://research.google/pubs/complex-dynamics-in-autobidding-systems/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Autobidder's Dilemma: Why Better Autobidders Lead to Worse Auction Efficiency](https://research.google/pubs/autobidders-dilemma-why-better-autobidders-lead-to-worse-auction-efficiency/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Incentive Compatibility in the Auto-bidding World](https://research.google/pubs/incentive-compatibility-in-the-auto-bidding-world/) | 2026-10-14 | 2026-10-14 |
| [Google Research - The Landscape of Autobidding Auctions: Value versus Utility Maximization](https://research.google/pubs/the-landscape-of-autobidding-auctions-value-versus-utility-maximization/) | 2026-10-14 | 2026-10-14 |
| [Google Research - Robust Budget Pacing with a Single Sample](https://research.google/pubs/robust-budget-pacing-with-a-single-sample/) | 2026-10-14 | 2026-10-14 |
