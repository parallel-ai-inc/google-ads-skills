# Parallel AI for Google Ads — Free Google Ads Agent Skills for Claude Code, Codex, and Cursor

Thirteen free, publicly inspectable **Google Ads Agent Skills** for **Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, Windsurf, and OpenCode**.

Built for real Google Ads audit, optimization, and campaign management jobs on downloaded Google Ads CSV exports — including **account audits, search terms and negative keywords, conversion tracking debugging, budget pacing, bidding and scaling, Performance Max and Shopping reviews, Search campaign builds, experiments, and Word client reports**, plus a **Live data** skill that configures Google's open-source read-only Google Ads MCP server on your own Google Cloud project.

- **Deterministic Python 3 math:** Local Python 3 standard-library scripts compute every metric, deduplicate wasted spend, and test every proposed negative keyword against converting searches. Your AI agent never invents figures.
- **Auditable rules:** Every check and recommendation is labelled **Official** (sourced from Google Ads documentation) or **Practitioner rule** (from Parallel AI's operating playbooks).
- **Zero live account edits & zero network calls:** Every script runs locally on your exports with no network requests, no telemetry, and no account credentials sent to Parallel AI. Wherever a job produces edits, the skill writes a **Google Ads Editor CSV with every new item paused** for your review.
- **Public and source-available:** Every `SKILL.md` file, playbook, reference file, and Python script is public on GitHub to inspect, audit, and run locally for personal or agency client work (see [License](#license)).

Full documentation and real sample outputs for every skill: **[withparallel.ai/skills](https://www.withparallel.ai/skills)**

---

## Install

### Every tool that reads Agent Skills (Cursor, Codex, Gemini CLI, Antigravity, GitHub Copilot, Windsurf, OpenCode, Claude Code)

```sh
npx skills add parallel-ai-inc/google-ads-skills -g
```

Install a single skill by name (for example, the Google Ads account audit skill):

```sh
npx skills add parallel-ai-inc/google-ads-skills --skill account-audit-for-google-ads -g
```

Add `-a <tool>` (`claude-code`, `codex`, `cursor`, `gemini-cli`, `github-copilot`, `windsurf`, `opencode`, `antigravity`) to target one tool. Omit `-g` to install only in the current project. Cursor also loads skills installed for Claude Code or Codex.

### Claude Code (plugin marketplace)

Run inside a Claude Code session:

```text
/plugin marketplace add parallel-ai-inc/google-ads-skills
/plugin install parallel-ai-for-google-ads@parallel-ai
```

On Claude Code 2.1.275 or later, one line does both: `/plugin install parallel-ai-for-google-ads --marketplace parallel-ai-inc/google-ads-skills`.

### OpenAI Codex (plugin marketplace)

```sh
codex plugin marketplace add parallel-ai-inc/google-ads-skills
codex plugin add parallel-ai-for-google-ads@parallel-ai
```

---

## The 13 Google Ads Agent Skills

| Group | Skill | Folder / Install Name | What It Does | Outputs & Docs |
|---|---|---|---|---|
| **Find wasted spend** | Account audit | `account-audit-for-google-ads` | Full Google Ads audit, readiness check before scaling, or post-change QA pass | Deduplicated waste, ordered fix plan (`account-audit.xlsx`, `.md`, `.json`) — [Docs](https://www.withparallel.ai/skills/account-audit-for-google-ads) |
| **Find wasted spend** | Search terms & negative keywords | `search-terms-for-google-ads` | Score every search term and test negatives so they block no converting searches or active keywords | Verdict workbook + paused Google Ads Editor CSV + account-level list — [Docs](https://www.withparallel.ai/skills/search-terms-for-google-ads) |
| **Diagnose performance** | Conversion tracking | `conversion-tracking-for-google-ads` | Audit and debug broken or double-counting conversion actions | Break dates, before/after leads per day, site check list by owner — [Docs](https://www.withparallel.ai/skills/conversion-tracking-for-google-ads) |
| **Diagnose performance** | Performance diagnosis | `performance-diagnosis-for-google-ads` | Isolate what changed, which campaign carried it, which lever moved, and when | Root-cause timeline matched to account change history — [Docs](https://www.withparallel.ai/skills/performance-diagnosis-for-google-ads) |
| **Diagnose performance** | Performance reviews | `performance-reviews-for-google-ads` | Weekly account review plus segment verdicts across keywords, QS, ads, devices, locations, schedule, pages, audiences, placements, and video | Weekly review workbook and Markdown brief — [Docs](https://www.withparallel.ai/skills/performance-reviews-for-google-ads) |
| **Diagnose performance** | Competition & market | `competitive-and-market-for-google-ads` | Auction insights, impression share lost to rank vs. budget, and seasonality | Competitor movement, share-of-voice, and seasonal workbook — [Docs](https://www.withparallel.ai/skills/competitive-and-market-for-google-ads) |
| **Budgets & bidding** | Budgets & forecasts | `budgets-and-forecasts-for-google-ads` | Monthly budget pacing and forecasts with Google's 30.4x monthly spending limits | Pacing workbook, holdout flags, and exact daily budget steps — [Docs](https://www.withparallel.ai/skills/budgets-and-forecasts-for-google-ads) |
| **Budgets & bidding** | Bidding & scaling | `bidding-and-scaling-for-google-ads` | Bid strategy review, step-sized scaling plan, wait windows, and rollback lines | Phased change plan + Google Ads Editor CSVs — [Docs](https://www.withparallel.ai/skills/bidding-and-scaling-for-google-ads) |
| **Build campaigns** | Campaign build | `campaign-build-for-google-ads` | Build a new Search campaign from a brief, checked against Google Ads limits and existing campaigns | Paused Google Ads Editor CSV (`EU political ads` + `AI Max` explicit) + owner launch checklist — [Docs](https://www.withparallel.ai/skills/campaign-build-for-google-ads) |
| **Build campaigns** | Performance Max & Shopping | `performance-max-for-google-ads` | Review PMax channel mix, asset groups, brand share, Shopping products, and Merchant Center price benchmarks | PMax workbook, findings brief, and launch/clone checklist — [Docs](https://www.withparallel.ai/skills/performance-max-for-google-ads) |
| **Report & prove results** | Client reporting | `client-reporting-for-google-ads` | Generate a white-label Word client report traced to data, or fact-check an existing draft | Branded `client-report.docx` + draft fact-check report — [Docs](https://www.withparallel.ai/skills/client-reporting-for-google-ads) |
| **Report & prove results** | Experiments | `experiments-for-google-ads` | Power/duration sizing for Google Ads experiments and geo-lift incrementality readouts | Days required, confidence/trust verdict, and margin-adjusted profit — [Docs](https://www.withparallel.ai/skills/experiments-for-google-ads) |
| **Live data** | Live data (Google Ads MCP) | `live-data-for-google-ads` | Read-only live pulls via Google's official open-source Google Ads MCP server on your own Google Cloud project | Live exports formatted in the exact CSV layout the other 12 skills expect — [Docs](https://www.withparallel.ai/skills/live-data-for-google-ads) |

---

## Local Agent Skills vs. Generic Prompt Packs vs. Parallel AI Platform

| Dimension | Parallel AI for Google Ads (This Free Repo) | Generic Prompt / Multi-Channel Skills | Parallel AI Platform ([withparallel.ai](https://www.withparallel.ai)) |
|---|---|---|---|
| **Google Ads depth** | 13 specialized Google Ads skills with 41 playbooks and Google-cited vs. practitioner rules | General marketing checklists across channels | Long-horizon AI agents built exclusively for Google Ads knowledge work |
| **Calculations & guardrails** | Deterministic local Python 3 scripts (zero LLM math, waste deduplicated once, negative keyword collision tests) | Prompt-only LLM reasoning | Live Google Ads API queries + structured verification and readback |
| **Account connection** | None required — runs on downloaded Google Ads CSV exports (or optional read-only Google Ads MCP on your own Cloud project) | Usually none or ad-hoc wrappers | Direct official Google Ads API OAuth across single or multi-client manager (MCC) accounts |
| **Applying changes** | Never touches your account; writes paused Google Ads Editor CSVs for manual import | Manual copy-paste | Applies reviewed changes in Google Ads under per-chat permission levels (`Plan only`, `Ask before changes`, `Auto-apply`, `Full`) |
| **Deliverables & research** | Local `.xlsx`, `.md`, `.docx`, `.csv`, `.txt` files | Text replies in chat | Built-in **Docs**, **Sheets**, **Deep Research**, and image/video asset generation |
| **Best fit** | Practitioners running free local audits, reviews, pacing, and builds in Claude Code, Codex, or Cursor | Light brainstorming | Agencies, in-house teams, and specialists running live multi-account Google Ads work ($20–$225/mo, 5-day free trial) |

---

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

---

## Frequently Asked Questions

### Are these Google Ads audit and management skills open source and free?

All 13 skills are **free to use** for your own Google Ads accounts or for client agency work, and the complete source code (`SKILL.md` instructions, playbooks, references, and Python 3 scripts) is **publicly inspectable on GitHub** at `github.com/parallel-ai-inc/google-ads-skills`. The repository is licensed under **PolyForm Shield 1.0.0** with an explicit written permission for personal and client Google Ads work — meaning any team can inspect, audit, and run the skills locally, while others cannot republish the pack as a competing skills product.

### How do I pull live Google Ads data into Claude Code, Codex, or Cursor via MCP?

Use the included **`live-data-for-google-ads`** skill. It guides read-only setup of **Google's own open-source Google Ads MCP server** (`googleads/google-ads-mcp`) on your own Google Cloud project and writes live reports in the exact CSV layout the other 12 skills read.

### Is Parallel AI (`withparallel.ai`) the same company as `parallel.ai`?

No. **Parallel AI, Inc.** ([withparallel.ai](https://www.withparallel.ai)) builds the AI agent platform for Google Ads and maintains this repository. It is unrelated to Parallel Web Systems (`parallel.ai`), Parallel Labs (`parallellabs.app`), or Google Ads Parallel Tracking.

---

## License

PolyForm Shield 1.0.0, with one additional permission: use the skills for any Google Ads work, for yourself or for clients, paid or unpaid. You may not publish them, changed or unchanged, as your own skills, plugin or similar product. See `LICENSE`.

*Google Ads is a trademark of Google LLC. Parallel AI is not affiliated with or endorsed by Google.*
