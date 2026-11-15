# Read only live access to Google Ads: your setup checklist

Every step happens in your own Google Cloud project and your own AI tool. Nothing here runs on anyone else's access.
Never paste a token, key, client secret or the contents of a credentials file into a chat, this one included. You run the sign in yourself.

Do the steps in order. Stop and tell your AI tool at the two checkpoints: after step 7 (you are signed in) and after step 9 (the tools appear). Every command below is filled in. Copy it as it is.

- Project: northside-ads-reports
- Google Ads account: 123-456-7890
- Client file: /Users/you/Downloads/client_secret_example.apps.googleusercontent.com.json

## 1. Check that your AI tool can run a local server
Desktop and command line AI tools that run on your computer can. Chat in a web browser cannot: use the downloaded exports instead.
**Confirm:** your AI tool has a place to add a local (stdio) MCP server.

## 2. Install Python 3.10 or later, pipx and the Google Cloud CLI
**Confirm:** `python3 --version` shows 3.10 or later, and `pipx --version` and `gcloud --version` both answer.

## 3. Use a Google Cloud project of your own
**Confirm:** `gcloud projects describe northside-ads-reports` shows the project.

## 4. Turn on the Google Ads API in that project
Run: `gcloud services enable googleads.googleapis.com --project northside-ads-reports`
**Confirm:** `gcloud services list --enabled --project northside-ads-reports` lists googleads.googleapis.com.

## 5. Apply for Explorer access, so the server can read real accounts
Turning on the API gives Test access, which reaches test accounts only. In the Cloud console, with project northside-ads-reports selected, open APIs and services, then Google Ads API, then its Overview page. It shows your current access level as Test. Expand Upgrade access level, check that the next access level is Explorer, and click Apply for access. Google may upgrade the project to Explorer automatically after you apply.
Explorer allows 2,880 operations a day against real accounts. It does not allow planning (such as keyword planning), account creation, user management or billing, none of which this skill uses.
**Confirm:** the Overview page shows your current access level as Explorer.

## 6. Set up the sign in screen and a Desktop app client
In the Cloud console, set up the OAuth consent screen, then create an OAuth client of type Desktop app and download its JSON file to /Users/you/Downloads/client_secret_example.apps.googleusercontent.com.json. Keep that file on your computer. Do not open it in a chat or paste it anywhere.
If the consent screen stays in Testing, add yourself as a test user. In Testing, your sign in expires after 7 days, and you repeat step 7.
**Confirm:** the file is at /Users/you/Downloads/client_secret_example.apps.googleusercontent.com.json.

## 7. Sign in, yourself, in your own terminal
Run this in a terminal, not in the chat:

```
gcloud auth application-default login --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform --client-id-file=/Users/you/Downloads/client_secret_example.apps.googleusercontent.com.json
```

A browser opens. Sign in with the Google account that has access to your Google Ads accounts, and allow access.
**Confirm:** the terminal says the credentials were saved, to /Users/you/.config/gcloud/application_default_credentials.json. That file holds your sign in. Never open, paste or share it.

**Checkpoint 1.** Tell your AI tool you are signed in. Say only that the credentials were saved. Do not paste anything from the file.

## 8. Check the read only settings file
This folder holds tools_config.yaml, which turns the server's write tools (assets and labels) off.
Run: `python3 /Users/you/Developer/google-ads-skills/skills/live-data-for-google-ads/scripts/setup.py --verify-config /Users/you/Developer/google-ads-skills/examples/output/live-data/setup/tools_config.yaml`
**Confirm:** it says Read only.

## 9. Add the server to your AI tool
In a command line AI tool that adds servers with `claude mcp add`, run this one line in a terminal:

```
claude mcp add google-ads --scope user -e GOOGLE_APPLICATION_CREDENTIALS=/Users/you/.config/gcloud/application_default_credentials.json -e GOOGLE_PROJECT_ID=northside-ads-reports -e GOOGLE_ADS_MCP_TOOLS_CONFIG=/Users/you/Developer/google-ads-skills/examples/output/live-data/setup/tools_config.yaml -- pipx run --spec google-ads-mcp==0.0.6 google-ads-mcp
```

Other tools: add a local (stdio) MCP server named google-ads from mcp-server.json in this folder, or from mcp-server.toml if the tool keeps its settings in TOML. Either way the server runs `pipx run --spec google-ads-mcp==0.0.6 google-ads-mcp`, pinned to one version, with:
- GOOGLE_APPLICATION_CREDENTIALS: /Users/you/.config/gcloud/application_default_credentials.json, the path to the file from step 7, never its contents.
- GOOGLE_PROJECT_ID: northside-ads-reports.
- GOOGLE_ADS_MCP_TOOLS_CONFIG: /Users/you/Developer/google-ads-skills/examples/output/live-data/setup/tools_config.yaml, the read only settings.
- No manager account is set. If the account sits under a manager account, run setup again with --login-customer.
Never set GOOGLE_ADS_MCP_OAUTH_CLIENT_ID or GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET. They turn the server from a local process into a web server.
**Confirm:** start a new session of your AI tool. Where it has the `/mcp` command, type `/mcp` and open google-ads. It shows exactly three tools: customers_list_accessible_customers, search_search, metadata_get_resource_metadata. If it shows create_asset, upload_video_asset, manage_labels or manage_label_associations under any prefix, stop: the read only file is not in use. Remove the server, check step 8, and add it again.

**Checkpoint 2.** Tell your AI tool which tools appear.

## 10. The final check, run by your AI tool
It runs: `python3 /Users/you/Developer/google-ads-skills/skills/live-data-for-google-ads/scripts/queries.py check --customer 123-456-7890 --work /Users/you/Developer/google-ads-skills/examples/output/live-data/setup/work`
Then it lists the accounts your sign in reaches and runs one small search for the account's name, currency and time zone.
**Confirm:** the name and currency are your account's.

## If something fails
- A sign in error after a week: the consent screen is in Testing. Repeat step 7.
- The account is not listed: sign in with a Google account that has access to it, or set the manager account and add the server again.
- An error about test accounts: Explorer access from step 5 is not in place yet.
