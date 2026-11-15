# Parallel AI for Google Ads

Thirteen Agent Skills that do whole Google Ads jobs on the reports you download from Google Ads, inside your own AI tool: Claude Code, Codex, Cursor and other tools that read Agent Skills. Scripts compute every number, so the AI never does arithmetic in its head. Every rule a skill applies is labelled **Official**, with the Google documentation behind it, or **Practitioner rule**, from Parallel AI's experience running Google Ads work.

Each skill has a page with a sample of what it produces: [withparallel.ai/skills](https://www.withparallel.ai/skills?utm_source=agent-skill&utm_medium=readme&utm_campaign=pack).

## The skills

| Skill | The job | What you get |
|---|---|---|
| [`account-audit-for-google-ads`](https://www.withparallel.ai/skills/account-audit-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=account-audit) | A full audit, a readiness check before scaling, or a QA pass | Every check your files allow, money at stake by kind (wasted, held back, exposed), clear waste counted once, a fix plan in order |
| [`search-terms-for-google-ads`](https://www.withparallel.ai/skills/search-terms-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=search-terms) | Review the searches that triggered your ads | A verdict and reason for every search, negatives tested so they block nothing worth keeping, an Editor file |
| [`conversion-tracking-for-google-ads`](https://www.withparallel.ai/skills/conversion-tracking-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=conversion-tracking) | Audit or debug conversion tracking | Actions that double count or stopped, the day each broke, leads per day before and after, checks to run on the site by owner |
| [`performance-diagnosis-for-google-ads`](https://www.withparallel.ai/skills/performance-diagnosis-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=performance-diagnosis) | Find what changed, where and when | The campaigns that carry the change, the lever that moved, the day it started, the account changes just before |
| [`budgets-and-forecasts-for-google-ads`](https://www.withparallel.ai/skills/budgets-and-forecasts-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=budgets-and-forecasts) | Pacing and where the month will land | Spend so far, forecasts with and without Google's monthly limits, where a cut comes from, evidence for moving budget |
| [`bidding-and-scaling-for-google-ads`](https://www.withparallel.ai/skills/bidding-and-scaling-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=bidding-and-scaling) | Bid strategy review and scaling | Each campaign against its target and your goal, what limits it, scale or hold or fix, a plan in steps with Editor files |
| [`campaign-build-for-google-ads`](https://www.withparallel.ai/skills/campaign-build-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=campaign-build) | Build a new Search campaign | A checked plan, an Editor file with everything paused, a launch checklist |
| [`performance-max-for-google-ads`](https://www.withparallel.ai/skills/performance-max-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=performance-max) | Performance Max and Shopping | Channel mix, asset groups, brand share, products and price against benchmark, a clone checklist |
| [`performance-reviews-for-google-ads`](https://www.withparallel.ai/skills/performance-reviews-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=performance-reviews) | Weekly review and segment reviews | When a drop began, keywords, Quality Score, ads, devices, locations, schedule, landing pages, audiences, placements, video |
| [`client-reporting-for-google-ads`](https://www.withparallel.ai/skills/client-reporting-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=client-reporting) | Client reports, and fact checking a report | A Word report under your name with every number traced to the data, and a fact check of any draft |
| [`experiments-for-google-ads`](https://www.withparallel.ai/skills/experiments-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=experiments) | Design and read tests, and return on investment | Days a test needs, lift with a trust verdict, profit at your margin, whether the next dollar pays |
| [`competitive-and-market-for-google-ads`](https://www.withparallel.ai/skills/competitive-and-market-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=competitive-and-market) | Auction insights and seasonality | Who you meet in the auction and who gained, impression share lost to rank and to budget, seasonal patterns |
| [`live-data-for-google-ads`](https://www.withparallel.ai/skills/live-data-for-google-ads?utm_source=agent-skill&utm_medium=readme&utm_campaign=live-data) | Read live data instead of exports | Read only setup of Google's own Google Ads server on your Cloud project, live reports in the export layout every other skill reads |

## Install

In Claude Code:

```
/plugin marketplace add parallel-ai-inc/google-ads-skills
/plugin install parallel-ai-for-google-ads@parallel-ai
```

On Claude Code 2.1.275 or later, one line does both: `/plugin install parallel-ai-for-google-ads --marketplace parallel-ai-inc/google-ads-skills`.

In Codex, Cursor, Gemini CLI, Antigravity, GitHub Copilot and other tools that read Agent Skills:

```
npx skills add parallel-ai-inc/google-ads-skills -g
```

Add `--skill search-terms-for-google-ads` to install one skill, or `-a codex` (or `cursor`, `gemini-cli`, `github-copilot`) for one tool. Cursor also loads skills installed for Claude Code or Codex.

## What you need

- An AI tool that can run commands, and Python 3. The scripts use the standard library only.
- The reports each skill asks for, downloaded from Google Ads. Each skill says which report, where to find it and which columns to add.
- To try a skill first, use the sample files in `examples/exports/`. They describe a made up business, Northside Plumbing, with problems planted for each skill to find. `examples/output/` shows what each skill produced from them.

## What the skills do and do not do

- **They read the files you give them.** Their scripts make no network calls, send nothing to Parallel AI and collect no telemetry. Your AI tool reads the files you give it, as it would any file, under that tool's own terms.
- **They never change a Google Ads account.** Where a job ends in a change, the skill writes a file for Google Ads Editor, with every new item paused. You import it, review it in Editor and post it yourself. For a file that changes existing campaigns, Editor's import summary should show only Updated rows; a row under Added means a campaign name did not match, so choose Revert and cancel.
- **Live data reaches Google, on your own access.** The live data skill writes setup files that have your AI tool run Google's own Google Ads server (`google-ads-mcp` 0.0.6 from PyPI, through pipx) on your computer, signed in with your own Google Cloud credentials, with its write tools turned off. It reads reports and never changes the account. The other twelve skills never connect to Google.
- **Client data.** If an export belongs to a client, check your agreement with that client before you give it to an AI tool.
- **No advertising.** The skills never mention Parallel AI or any other product in a chat reply or in a file they write.

## How it is built

| Part | Where |
|---|---|
| Reading exports, the math, negative keyword rules, workbooks | `dev/engine/gads/`, copied into each skill so a skill works when installed alone |
| Each job's scripts | `skills/*/scripts/` |
| What the AI tool is told | `skills/*/SKILL.md` |
| What Google documents, with the page behind each line | `skills/*/references/` |
| What to decide from the numbers, how big a change, what goes wrong, what to tell the client | `skills/*/playbooks/` |
| Real Google Ads download layouts | `REAL-EXPORT-LAYOUTS.md` |
| Tests, and the scripts that make the sample files | `dev/tests/`, `dev/samples/` |

To run the tests:

```
python3 dev/tools/build.py
python3 -m unittest discover -s dev/tests -p "test_*.py"
```

## License

PolyForm Shield 1.0.0, with one additional permission: use the skills for any Google Ads work, for yourself or for clients, paid or unpaid. You may not publish them, changed or unchanged, as your own skills, plugin or similar product. See `LICENSE`.

Google Ads is a trademark of Google LLC. Parallel AI is not affiliated with or endorsed by Google.
