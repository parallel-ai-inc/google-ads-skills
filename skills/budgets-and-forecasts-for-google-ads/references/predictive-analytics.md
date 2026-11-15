<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## PREDICTIVE ANALYTICS METHODS

### Prophet Time-Series Forecasting
**Use Case:** Seasonal pattern detection and revenue forecasting

**Components:**
- Trend: Long-term trajectory
- Seasonality: Weekly, monthly, yearly patterns
- Holiday effects: Special events impact
- Changepoints: Trend shifts

**Application:** Budget planning, seasonal bidding adjustments, spend pacing

### Counterfactual LSTM Models
**Use Case:** Dynamic budget scenario planning

**Mechanism:**
- Train on historical performance data
- Generate "what-if" scenarios for budget changes
- Predict conversion/revenue impact of allocation shifts

**Application:** Budget optimization, expansion planning, risk assessment

### SHAP Value Analysis (Analyst-Side Method)
**Use Case:** Feature weighting inside your own models

**Mechanism:**
- Shapley values from cooperative game theory
- Measures each feature's contribution to predictions
- Identifies most impactful signals

**Application:**
- Understanding which audience signals drive conversions in your own data
- Explaining your own models; Smart Bidding's own signal view is the bid strategy report's top signals
- Not a view into Smart Bidding: most automated strategies ignore manual bid modifiers other than device

### Hierarchical Bayesian Inference (Analyst-Side Method)
**Use Case:** Cold start and small data scenarios in your own forecasts

**Example Pooling Hierarchy (your model, not Google's):**
1. L1 (Query): Direct conversion data
2. L2 (Ad Group): Pooled variance
3. L3 (Campaign/Account): Account-level priors
4. L4 (Vertical): Benchmarks you supply

**"Shrinkage" Effect:** Estimates for small-data entities pulled toward group mean

**What Google says about Smart Bidding:** conversion-rate models seeded with query-level data when conversion data is thin, refined with Bayesian learning, with recent data weighted by conversion-cycle length. Google doesn't publish pooling levels or global priors.

### Anomaly Detection
**Z-Score Method:**
`Z_Score = (current_value - moving_avg) / moving_stddev`
- Flag if: |Z_Score| > 2.0
- Rolling window: 28 days

**Application:** Performance monitoring, early warning systems

### Multi-Armed Bandit Optimization
**Use Case:** Dynamic resource allocation

**Mechanism:**
- Balance exploration vs exploitation
- Allocate budget to highest-performing "arms" (campaigns)
- Thompson Sampling for probability matching

**Application:** Budget distribution, audience testing, creative rotation

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
