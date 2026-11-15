<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## TARGET CPA SMART BIDDING FRAMEWORK

This topic is internal practitioner guidance. It describes how to work a tCPA strategy with account evidence, not a universal platform rulebook.

### Setup Principles
- Define one primary conversion that reflects the business outcome you actually want to buy.
- Compare the current target against recent realized CPA while accounting for conversion delay.
- Check budget headroom, bid strategy status, search-term quality, landing-page quality, conversion integrity, and any Google recommendation to raise Target CPA because the target is too low, before concluding the target is wrong.

### Decision Rules
| Condition | Operator move |
|-----------|---------------|
| CPA below target and volume constrained | Consider budget expansion first, then a modest tCPA increase if the business wants more volume |
| CPA above target but traffic quality is strong | Fix funnel, offer, or landing-page issues before repeatedly tightening the target |
| CPA above target and strategy is clearly too loose | Set tCPA to the CPA the business will accept and re-evaluate after 1-2 conversion cycles |
| Signal volume too thin for stable tCPA behavior | Maximize conversions builds volume; Google's About Target CPA bidding page says Target CPA can start with no conversion history, while its Tips on measuring Smart Bidding performance page suggests Maximize clicks or Manual CPC to build conversion data first. Choose by the business's tolerance for cost swings |

### Adjustment Discipline
- Google's Search bidding guide says Smart Bidding reacts immediately to target changes of any size without resetting learning, so on Search and Shopping the size of a move is a business-risk choice: a large target move changes spend or volume by a similar amount, and a step that enters a new set of auctions can bring short volatility. Some older Google troubleshooting pages still recommend smaller changes; when risk tolerance is low, step the target and read each step after 1-2 conversion cycles.
- Evaluate changes over 2 full conversion cycles whenever possible; short windows can misread lagged conversions.
- Use bid strategy reports and simulators before major budget or target changes.

### Common Failure Modes
- Primary conversion is low-quality or duplicated.
- Recent attribution or value-setting changes are distorting the read.
- Search terms and landing pages do not support the CPA target you want.
- The business wants sales-qualified outcomes but the campaign is optimizing for a cheaper proxy event.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
