<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## TARGET ROAS SMART BIDDING FRAMEWORK

This topic is internal practitioner guidance. Use it with current target ROAS Help Center requirements and live account evidence.

### Setup Principles
- Verify that conversion values are trustworthy, differentiated, and aligned to business value.
- Confirm the campaign type actually meets current target ROAS readiness guidance before switching.
- If Search values were recently added or changed, wait 1-2 conversion cycles for values to arrive at a similar rate before adopting Target ROAS.
- Before concluding the target is wrong, check bid strategy status, search impression share lost to rank, and any Google recommendation to lower Target ROAS because the target is too high.

### Decision Rules
| Condition | Operator move |
|-----------|---------------|
| Actual ROAS is above target and the business wants more volume | Consider a modest target reduction or budget expansion |
| Actual ROAS is below target and traffic quality is still strong | Audit value quality, search terms, landing page, and pricing before only tightening the target |
| Actual ROAS is below target because bids are clearly too loose | Set tROAS to the return the business needs and re-evaluate after 1-2 conversion cycles |
| Value density is too thin for a stable tROAS read | Prefer Maximize conversion value while value tracking matures |

### Adjustment Discipline
- Google says Smart Bidding reacts immediately to target changes of any size without resetting learning, while its Target ROAS page still suggests reducing a target gradually; treat the step size as a business-risk choice, avoid several Target ROAS changes inside one conversion cycle when you need a clean read, and account for conversion delay.
- Prefer bid strategy reports, simulators, and business economics over canned numeric playbooks.
- Keep margin, refund risk, and sales quality in the conversation; ROAS alone is not profit.

### Common Failure Modes
- Revenue values are missing, duplicated, or delayed.
- The account mixes lead proxies and closed revenue in one optimization signal.
- The target is imported from another business model without considering margin or conversion lag.
- Search demand, competition, or price position changed and the target was blamed first.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
