# What real Google Ads downloads look like

Read from real downloads on 2026-11-13, taken from the Google Ads web interface with the Download button. Loaders must handle everything on this page. The engine's `io.read_report` already does.

The raw files are kept outside this repository. Nothing here is account data. It is layout only.

## Every report

- **Row 1** is the report name, for example `Search terms report`.
- **Row 2** is the date range in quotation marks, for example `"November 11, 2026 - November 13, 2026"`.
- **Row 3** is the header.
- **Empty cells** are written as ` --` with a leading space, or left blank.
- **Numbers** use thousands separators and are quoted when they do: `"3,451"`. Percentages carry the sign: `0.67%`.
- **Money** is a plain number, `28.50`, with the currency in its own `Currency code` column. Some custom columns carry a symbol, `$0.00`.
- **Accounts add their own columns,** such as custom conversion columns. Ignore headers you do not know.

## The three download formats

| Menu item | What arrives |
|---|---|
| `.csv` | Plain text, commas |
| `Excel .csv` | UTF-16 text, tabs |
| `.xlsx` | A workbook with the same rows |

All three load through `io.read_report` and give the same rows.

## Total rows

Total rows come after the data. They are not always the ones the samples in this pack first assumed.

- **Search terms report:** `Total: Account`, then one per campaign type: `Total: Search`, `Total: Demand Gen`, `Total: Performance Max`.
- **Campaign report:** `Total: Filtered campaigns`, `Total: Account`, and one per campaign type.
- **Keyword report:** `Total: Keywords in your account`, `Total: All but removed keywords`, `Total: AI Max expanded matches`, `Total: AI Max landing page matches`, `Total: Account`, and one per campaign type.
- **When a report is segmented by Day,** each total row starts with the date, and `Total: ...` is in the second column: `2026-11-12,Total: Search,,...`. A loader that only looks at the first cell will read these as data.

Not yet seen in a real file: the total rows of a search terms report that has search rows in it. The sample here writes `Total: Search terms` and `Total: Other search terms`, which is unconfirmed.

## Headers seen

**Search terms report**

`Search term, Match type, Added/Excluded, Campaign, Ad group, Keyword, Currency code, Avg. CPM, Clicks, Impr., CTR, Avg. CPC, Cost, Campaign type, Conv. rate, Conversions, Cost / conv.`

**Campaign report**

`Campaign status, Campaign, Budget, Budget name, Budget type, Currency code, Status, Status reasons, Campaign type, Bid strategy type, Cost, Impr., Clicks, CTR, Avg. CPC, Search impr. share, Search lost top IS (rank), Search lost top IS (budget), Conv. rate, Conversions, Cost / conv., Goals`

- `Campaign status` is Enabled or Paused. `Status` is the serving status, such as `Eligible (Learning)`.
- `Budget` is the daily amount as a plain number. `Budget type` says `Daily`.
- `Bid strategy type` reads `Maximize Conversions`, with a capital C.
- Segmented by Day, a `Day` column comes first, written `2026-11-11`.

**Keyword report** (its report name is `Search keyword report`)

`Keyword status, Keyword, Match type, Campaign, Ad group, Status, Status reasons, Final URL, Currency code, Avg. CPM, Impr., Interactions, Interaction rate, Avg. cost, Cost, Conv. rate, Conversions, Cost / conv.`

- The `Keyword` column carries the match type symbols: `[exact]`, `"phrase"`, and plain text for broad.
- This account's columns show `Interactions` and `Avg. cost`, not `Clicks` and `Avg. CPC`. A loader should accept either.

**Change history** (its report name is `Change history report`)

`Date & time, User, Campaign, Ad group, Changes`

- `Date & time` is written `"Nov 13, 2026, 11:00:41 AM"`.
- `Changes` can run over several lines inside one quoted cell.
- `Campaign` and `Ad group` are blank for account level changes.

### Ads report (downloaded 2026-11-14)

- Title `Ad report`, then the quoted date range, then the header. UTF-8 with a byte order mark, line feeds only.
- In an account that mixes Search, Demand Gen and Performance Max, the default view has 92 columns. There is no single `Ad` column: the ad's text is in `Headline 1` to `Headline 15` (each with a `Headline N position` column for pins), `Description 1` to `Description 5`, `Long headline 1` to `Long headline 5`, plus image, video and business name columns for visual ads. `Ad name` is filled for some ad types.
- Traffic columns use the cross-format names `Interactions`, `Interaction rate` and `Avg. cost`, not `Clicks`, `CTR` and `Avg. CPC`. The skills read `Interactions` as clicks and say so.
- `Status`, `Status reasons`, `Ad strength`, `Ad strength improvements` and `Ad type` are present. `Conv. (Platform Comparable)` columns sit beside `Conversions`.
- Total rows: `Total: All but removed ads`, `Total: Account`, then one per campaign type, such as `Total: Performance Max`, `Total: Demand Gen` and `Total: Search`. A per type total covers only that type.
- Read correctly by the account audit and performance reviews skills: rows reconcile to the file's own total.

### More reports (downloaded 2026-11-14)

Each was read by the skill that uses it, and its rows reconcile to the file's own total. These files had no byte order mark, so loaders must accept both.

| Report name in row 1 | Header (first columns) | Total rows | Read by |
|---|---|---|---|
| `Ad group report` | `Ad group status, Ad group, Campaign, ...`; `Currency code` appears twice | per campaign type and account | account audit, performance reviews |
| `Device report` | `Device, Level, Campaign, Ad group, Bid adj., Ad group bid adj., Currency code, ...` | `Total: Account` | performance reviews |
| `Ad schedule day and hour report` | `Day of the week, Hour of the day, Campaign, Currency code, ...`; hours are `0` to `23` | `Total: Campaigns`, `Total: Account`, one per campaign type | performance reviews |
| `Automatic placements report` | `Placement, Placement url, Type, Campaign, Ad group, ...`; `Type` is `YouTube channel`, `Site` or `Google products` | `Total: Where ads showed`, `Total: Account`, one per campaign type | performance reviews |
| `Matched locations report` | `Matched location, Clicks, Impr., CTR, ...`; no Campaign column at account level | `Total: Locations`, `Total: Account`, one per campaign type | performance reviews |
| `Audience segment report` | `Segment status, Audience segment, Type, Campaign, Ad group, Status, Status reasons, Level, Bid adj., ...` | `Total: Audiences`, `Total: Display automatic targeting`, `Total: Account`, one per campaign type | performance reviews |
| `Landing page report` | `Landing page, Selected by, Mobile speed score, Mobile-friendly click rate, Valid AMP click rate, Clicks, Impr., CTR, Currency code, Avg. CPC, Cost` | `Total: Landing pages`, `Total: Account`, one per campaign type | performance reviews, once Conversions is added |
| `Auction insights report` | `Display URL domain, Impression share, Overlap rate, Position above rate, Top of page rate, Abs. Top of page rate, Outranking share`; the own row is `You`; low shares are `< 10%` | none | competitive and market |

What these files changed in the skills:

- **Rounding.** Each row's cost is rounded to the cent and the total is worked out before rounding, so a placement report with 213 rows summed 0.05 away from its total. The performance reviews, account audit and competitive skills now allow half a cent a row before they call rows and total different, as conversion tracking, client reporting and experiments already did.
- **Long tails repeat.** 89 placements shared one interaction and 0.01 of cost. Identical figures are flagged only on segments with 10 clicks or more.
- **The landing page download has no Conversions column by default.** The skill says to add it under Columns.
- **Search lost top IS is not Search lost IS.** A campaign report can carry only the top of page versions. The competitive skill no longer reads them as share lost; the bidding skill reads them and labels them as top of page.
- **One auction insights file is still useful.** Unsegmented and alone, it now gives the table of who the account meets, and says nothing about who moved.

### Conversion actions (looked at 2026-11-14, not downloaded)

- The table is at Goals, Conversions, All conversions. Goals, Summary is now the goals overview. Its columns: `Conversion action, Conversion source, Tracking status, Action optimization, Count, Click-through conversion window, Included in account-level goals, All conv., All conv. value`, with rows grouped under category headings such as `Sign-ups`.
- That table had no Download button. Report editor's Conversions template downloads `Conversion action` with conversion columns and can add `Conversion source` and `Conversion category`, but it has no settings columns and lists only actions with conversions in the range. The conversion tracking skill says so and names the checks it skips.
- The account had no conversions yet, so no conversion file could be checked against real data.

## Not yet downloaded from a real account

A conversion actions file and a conversions by action and day file from an account with conversions, auction insights segmented by month, a campaign report by month with Search lost IS, and the Performance Max and Shopping reports. Skills that read these are built on Google's documented columns and each lists its assumptions.
