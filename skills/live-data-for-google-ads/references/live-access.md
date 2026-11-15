# Live access through Google's Google Ads MCP server

Written by hand. To be re-read against the source before release.

Read from the sources below on 2026-11-13. Each section names its source. Statements here are **Official** where a Google page or Google's own repository says them, and **Practitioner rule** where marked.

## The server

Source: [github.com/googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp), its README, Apache-2.0.

- Google's open source Google Ads MCP server. PyPI version 0.0.6. Run with `pipx run --spec "google-ads-mcp==0.0.6" google-ads-mcp`. Python 3.10 or later.
- It talks over stdio by default: the AI tool starts it as a local process on the person's computer.
- Setting `GOOGLE_ADS_MCP_OAUTH_CLIENT_ID` and `GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET` switches it to a web server (streamable HTTP). This skill never sets them and never runs the server as a web server.
- Read tools: `search` (GAQL built from structured parameters: customer_id, resource, fields, and optional conditions, orderings, limit and login_customer_id), `get_resource_metadata` and `list_accessible_customers`. Since 0.0.6 the names carry their category as a prefix: `search_search`, `metadata_get_resource_metadata`, `customers_list_accessible_customers`.
- Write tools: `create_asset`, `upload_video_asset`, `manage_labels`, `manage_label_associations` (prefixed `assets_` and `labels_`). **The server is not read only by default.** The README: "For strictly read-only deployments, set `labels: false` and `assets: false` in your `tools_config.yaml`."
- The server looks for `tools_config.yaml` at the path in `GOOGLE_ADS_MCP_TOOLS_CONFIG`, then in the folder it starts in, then uses its bundled default, which turns every tool on. A file named in the variable that is missing or invalid stops the server from starting.
- The README's file layout: a top level `namespaces:` map. `category: true` turns a category on with its default prefix, `category: false` turns it off.
- The search tool's result format is not documented in the README. The converter reads the common shapes and says so.

## Credentials

Source: the same README.

- Application Default Credentials, created by the person in their own terminal:
  `gcloud auth application-default login --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform --client-id-file=YOUR_CLIENT_JSON_FILE`
- The client configuration sets `GOOGLE_APPLICATION_CREDENTIALS` (a path), `GOOGLE_PROJECT_ID` and, for accounts under a manager, `GOOGLE_ADS_LOGIN_CUSTOMER_ID`.
- **Practitioner rule:** the credentials file and the client file hold secrets. They are referred to by path only. Nobody opens, prints or pastes them, and no AI tool asks for them.

## Access levels

Sources: [Developer token sunset](https://developers.google.com/google-ads/api/docs/api-policy/developer-token), [Access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels).

- Developer tokens were sunset on 2026-09-09. The Google Cloud project's access level decides access (also in `technical-integration.md`).
- Turning on the API gives Test access: test accounts only.
- Explorer access reaches real accounts at 2,880 operations a day and is approved automatically in most cases. It does not allow account creation, user management, planning (such as keyword planning) or billing and payment.
- To apply: open the Google Ads API Overview page in the Cloud project (APIs and services, Google Ads API). It shows the current access level as Test. Expand Upgrade access level, confirm the next level is Explorer, and click Apply for access. Google may upgrade the project automatically after the application. Once granted, the Overview page shows the current access level as Explorer. Read from the Access levels page on 2026-11-13.

## Sign in that expires

Source: [Google Identity, refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration).

- An external OAuth consent screen left in Testing issues refresh tokens that expire after 7 days. The person then signs in again.

## Fields checked by hand

Sources: Google's field reference for [search_term_view](https://developers.google.com/google-ads/api/fields/v22/search_term_view) and [ad_group_ad](https://developers.google.com/google-ads/api/fields/v22/ad_group_ad). The reference was read at v22; the pack's other references cite v25. Re-read at the current version.

- search_term_view lists ad_group, campaign and customer as attributed resources: their fields can be selected with it and do not segment its metrics.
- ad_group_ad lists ad_group, campaign and customer as attributed resources, and has the field `ad_group_ad.ad_strength`.
- `ad_group_ad.ad_strength` is the one field the named reports use that is not in `scripts/known_fields.json`.

## Change history

Source: [Change event](https://developers.google.com/google-ads/api/docs/change-event).

- The date range must be within the past 30 days. The query must filter on `change_event.change_date_time` and carry a LIMIT of at most 10,000 rows.
- Google's examples cover ads, ad groups, criteria, bid modifiers, assets and asset sets, campaigns, campaign budgets and feeds. The page does not list conversion actions.
- From the pack's own query library (`queries-by-resource.md`): Google returns only the latest change to each item in the window, and a change can take up to three minutes to appear.

## Values the converter writes as the interface does

To be re-read: the metric reference says impression shares below 10% are reported as 0.0999 and lost shares above 90% as 0.9001. The converter writes those as `< 10%` and `> 90%`, as downloads do. The words for API values (Exact match, Maximize Conversions, Sign-up) were written by hand from the interface and from the layouts in `REAL-EXPORT-LAYOUTS.md`.

## Google Ads scripts

Sources: [AdsApp.search](https://developers.google.com/google-ads/scripts/docs/reference/adsapp/adsapp), [SpreadsheetApp](https://developers.google.com/apps-script/reference/spreadsheet/spreadsheet-app), [Scripts limits](https://developers.google.com/google-ads/scripts/docs/limits) (also in `automation.md`).

- The scripts call `AdsApp.search` with GAQL to read, and `SpreadsheetApp.openByUrl` to write one tab of a Sheet the person owns. They call nothing that changes the account.
- They were written to these documented interfaces and have not been run in an account. The person runs Preview first.

## What not to present as fact

- Do not state the search tool's output format, beyond what the converter accepts.
- Do not state a daily operation count for a report: whether one search counts as one operation is not checked here.
- Do not say the server is read only unless the account check showed only the three read tools.
