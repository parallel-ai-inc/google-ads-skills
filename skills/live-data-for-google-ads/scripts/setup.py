#!/usr/bin/env python3
"""Write the files for read only live access to Google Ads, on the person's own
Google Cloud project, through Google's open source Google Ads MCP server.

    python3 scripts/setup.py --out SETUP_DIR --project-id my-ads-project --client-id-file PATH --customer 123-456-7890 [--login-customer 111-222-3333] [--work WORK] [--credentials-path PATH]
    python3 scripts/setup.py --verify-config SETUP_DIR/tools_config.yaml

Writes tools_config.yaml (the read only tool settings), mcp-server.json and
mcp-server.toml (the server entry for the AI tool, in the two common forms)
and setup-checklist.md (every step, with how to confirm it worked, and every
command filled in and ready to copy).

It never asks for, reads, prints or stores a token, key or client secret. The
config files hold only paths and IDs. The person signs in themselves.
"""
import argparse
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livecore as lc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = "google-ads-mcp==0.0.6"
COMMAND = ["run", "--spec", PACKAGE, "google-ads-mcp"]
SCOPES = "https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform"
READ_ONLY = {"customers": "true", "search": "true", "metadata": "true", "labels": "false", "assets": "false"}
WRITE_CATEGORIES = ("labels", "assets")
READ_TOOLS = (lc.LIST_TOOL, lc.SEARCH_TOOL, lc.METADATA_TOOL)
# Shapes of secrets. A value that looks like one is refused, never written.
# A path may name Google's downloaded client file (client_secret_....json); its contents may never be given.
SECRET_SHAPES = (r"GOCSPX-", r"\bya29\.", r"^1//", r"-----BEGIN", r"[{}]", r"\"(private_key|client_secret|refresh_token)\"",
                 r"AIza[0-9A-Za-z_\-]{20,}")
HTTP_VARIABLES = ("GOOGLE_ADS_MCP_OAUTH_CLIENT_ID", "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET")
ASK = ("Ask the person, in one message, for: (1) their Google Cloud project ID, shown on the project's dashboard in the Cloud "
       "console and in the project picker at the top; (2) the path of the Desktop app client file they downloaded, such as "
       "~/Downloads/client_secret_....json (the path only, never the file's contents); (3) the Google Ads account ID to read, "
       "shown with dashes at the top of Google Ads, such as 123-456-7890. With or without dashes is fine. "
       "Do not run setup with placeholders.")


def refuse_secret(name, value):
    for shape in SECRET_SHAPES:
        if value and re.search(shape, value, re.I):
            raise lc.Refusal("The value given for %s looks like a secret. Never paste a token, key or client secret here or in "
                             "the chat. Give the path to the file instead, and keep the file to yourself." % name)


def safe_path(name, value):
    refuse_secret(name, value)
    if value and (any(ch in value for ch in "\"'\n\r`$") or len(value) > 400):
        raise lc.Refusal("I can't use the path given for %s. Give a plain file path." % name)
    return os.path.abspath(os.path.expanduser(value)) if value else value


def default_credentials_path():
    if os.name == "nt":
        return os.path.join(os.environ.get("APPDATA", r"C:\Users\YOU\AppData\Roaming"), "gcloud", "application_default_credentials.json")
    return os.path.join(os.path.expanduser("~"), ".config", "gcloud", "application_default_credentials.json")


def tools_config():
    lines = ["# Google Ads MCP server: read only.",
             "# Only the read tools are on: list accessible customers, search, and resource metadata.",
             "# The write tools (assets and labels) are off. Keep them off.",
             "namespaces:"]
    lines += ["  %s: %s" % (k, v) for k, v in READ_ONLY.items()]
    return "\n".join(lines) + "\n"


def read_config(path):
    """The namespaces in a tools_config.yaml, from its simple two level layout."""
    if not os.path.isfile(path):
        raise lc.Refusal("I can't find %s. Write it with %s first." % (path, os.path.join(HERE, "setup.py")))
    found, inside, nested = {}, False, None
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            key, _, value = line.strip().partition(":")
            value = value.strip().strip('"').strip("'").lower()
            if indent == 0:
                inside = key == "namespaces"
                continue
            if not inside:
                continue
            if indent == 2:
                nested = None if value else key
                found[key] = value if value else {}
            elif nested and indent == 4 and key == "enabled":
                found[nested] = value
    return found


def verify(path):
    found = read_config(path)
    problems = []
    for category in WRITE_CATEGORIES:
        if found.get(category) != "false":
            problems.append("%s is not set to false" % category)
    extra = [k for k in found if k not in READ_ONLY]
    for key in extra:
        if found[key] != "false":
            problems.append("%s is a category this check does not know; set it to false" % key)
    if problems:
        print("NOT read only: %s. Write the file again with setup.py, or set labels: false and assets: false under namespaces." % "; ".join(problems))
        sys.exit(1)
    print("Read only: labels and assets are off%s. Only these tools should appear: %s." % (
        "" if not extra else ", and every other category is off", ", ".join(READ_TOOLS)))


def server_entry(project_id, credentials, config_path, login):
    env = {"GOOGLE_APPLICATION_CREDENTIALS": credentials, "GOOGLE_PROJECT_ID": project_id,
           "GOOGLE_ADS_MCP_TOOLS_CONFIG": config_path}
    if login:
        env["GOOGLE_ADS_LOGIN_CUSTOMER_ID"] = login
    return {"command": "pipx", "args": COMMAND, "env": env}


def toml(entry):
    quote = lambda text: json.dumps(text)  # noqa: E731  JSON strings are valid TOML basic strings
    lines = ["[mcp_servers.google-ads]", "command = %s" % quote(entry["command"]),
             "args = [%s]" % ", ".join(quote(a) for a in entry["args"]), "", "[mcp_servers.google-ads.env]"]
    lines += ["%s = %s" % (k, quote(v)) for k, v in entry["env"].items()]
    return "\n".join(lines) + "\n"


def add_command(entry):
    """The one line that adds the server from the command line, at user scope, with the read only file set."""
    parts = ["claude", "mcp", "add", "google-ads", "--scope", "user"]
    for key, value in entry["env"].items():
        parts += ["-e", "%s=%s" % (key, value)]
    parts += ["--", entry["command"]] + entry["args"]
    return " ".join(shlex.quote(p) for p in parts)


def checklist(project_id, credentials, config_path, client_file, login, customer, work, entry):
    q = shlex.quote
    login_line = ("- GOOGLE_ADS_LOGIN_CUSTOMER_ID: %s, your manager account, so accounts under it can be read." % login
                  if login else "- No manager account is set. If the account sits under a manager account, run setup again with --login-customer.")
    return """# Read only live access to Google Ads: your setup checklist

Every step happens in your own Google Cloud project and your own AI tool. Nothing here runs on anyone else's access.
Never paste a token, key, client secret or the contents of a credentials file into a chat, this one included. You run the sign in yourself.

Do the steps in order. Stop and tell your AI tool at the two checkpoints: after step 7 (you are signed in) and after step 9 (the tools appear). Every command below is filled in. Copy it as it is.

- Project: {project}
- Google Ads account: {customer}
- Client file: {client_file}

## 1. Check that your AI tool can run a local server
Desktop and command line AI tools that run on your computer can. Chat in a web browser cannot: use the downloaded exports instead.
**Confirm:** your AI tool has a place to add a local (stdio) MCP server.

## 2. Install Python 3.10 or later, pipx and the Google Cloud CLI
**Confirm:** `python3 --version` shows 3.10 or later, and `pipx --version` and `gcloud --version` both answer.

## 3. Use a Google Cloud project of your own
**Confirm:** `gcloud projects describe {project}` shows the project.

## 4. Turn on the Google Ads API in that project
Run: `gcloud services enable googleads.googleapis.com --project {project}`
**Confirm:** `gcloud services list --enabled --project {project}` lists googleads.googleapis.com.

## 5. Apply for Explorer access, so the server can read real accounts
Turning on the API gives Test access, which reaches test accounts only. In the Cloud console, with project {project} selected, open APIs and services, then Google Ads API, then its Overview page. It shows your current access level as Test. Expand Upgrade access level, check that the next access level is Explorer, and click Apply for access. Google may upgrade the project to Explorer automatically after you apply.
Explorer allows 2,880 operations a day against real accounts. It does not allow planning (such as keyword planning), account creation, user management or billing, none of which this skill uses.
**Confirm:** the Overview page shows your current access level as Explorer.

## 6. Set up the sign in screen and a Desktop app client
In the Cloud console, set up the OAuth consent screen, then create an OAuth client of type Desktop app and download its JSON file to {client_file}. Keep that file on your computer. Do not open it in a chat or paste it anywhere.
If the consent screen stays in Testing, add yourself as a test user. In Testing, your sign in expires after 7 days, and you repeat step 7.
**Confirm:** the file is at {client_file}.

## 7. Sign in, yourself, in your own terminal
Run this in a terminal, not in the chat:

```
gcloud auth application-default login --scopes {scopes} --client-id-file={client_file_q}
```

A browser opens. Sign in with the Google account that has access to your Google Ads accounts, and allow access.
**Confirm:** the terminal says the credentials were saved, to {credentials}. That file holds your sign in. Never open, paste or share it.

**Checkpoint 1.** Tell your AI tool you are signed in. Say only that the credentials were saved. Do not paste anything from the file.

## 8. Check the read only settings file
This folder holds tools_config.yaml, which turns the server's write tools (assets and labels) off.
Run: `python3 {setup} --verify-config {config_q}`
**Confirm:** it says Read only.

## 9. Add the server to your AI tool
In a command line AI tool that adds servers with `claude mcp add`, run this one line in a terminal:

```
{add_command}
```

Other tools: add a local (stdio) MCP server named google-ads from mcp-server.json in this folder, or from mcp-server.toml if the tool keeps its settings in TOML. Either way the server runs `pipx {command}`, pinned to one version, with:
- GOOGLE_APPLICATION_CREDENTIALS: {credentials}, the path to the file from step 7, never its contents.
- GOOGLE_PROJECT_ID: {project}.
- GOOGLE_ADS_MCP_TOOLS_CONFIG: {config}, the read only settings.
{login_line}
Never set {http_vars}. They turn the server from a local process into a web server.
**Confirm:** start a new session of your AI tool. Where it has the `/mcp` command, type `/mcp` and open google-ads. It shows exactly three tools: {read_tools}. If it shows create_asset, upload_video_asset, manage_labels or manage_label_associations under any prefix, stop: the read only file is not in use. Remove the server, check step 8, and add it again.

**Checkpoint 2.** Tell your AI tool which tools appear.

## 10. The final check, run by your AI tool
It runs: `python3 {queries} check --customer {customer} --work {work_q}`
Then it lists the accounts your sign in reaches and runs one small search for the account's name, currency and time zone.
**Confirm:** the name and currency are your account's.

## If something fails
- A sign in error after a week: the consent screen is in Testing. Repeat step 7.
- The account is not listed: sign in with a Google account that has access to it, or set the manager account and add the server again.
- An error about test accounts: Explorer access from step 5 is not in place yet.
""".format(project=project_id, customer=lc.dashed(customer), client_file=client_file, client_file_q=q(client_file), scopes=SCOPES,
           credentials=credentials, config=config_path, config_q=q(config_path), setup=q(os.path.join(HERE, "setup.py")),
           queries=q(os.path.join(HERE, "queries.py")), work_q=q(work), add_command=add_command(entry),
           command=" ".join(COMMAND), login_line=login_line, http_vars=" or ".join(HTTP_VARIABLES),
           read_tools=", ".join(READ_TOOLS))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", help="folder for the setup files")
    parser.add_argument("--project-id", help="your Google Cloud project ID, such as my-ads-project")
    parser.add_argument("--client-id-file", help="the path of the Desktop app client file you downloaded")
    parser.add_argument("--customer", help="the Google Ads account ID to read, with or without dashes")
    parser.add_argument("--login-customer", help="your manager account ID, to read accounts under it")
    parser.add_argument("--work", help="folder for live report files. Default: a work folder inside --out")
    parser.add_argument("--credentials-path", help="where the sign in file will be. Default: gcloud's own location")
    parser.add_argument("--verify-config", help="check that a tools_config.yaml is read only")
    parser.add_argument("--as-home", help=argparse.SUPPRESS)  # writes sample files with a placeholder home folder
    args = parser.parse_args()
    if args.verify_config:
        verify(args.verify_config)
        return
    missing = [name for name, value in (("--project-id", args.project_id), ("--client-id-file", args.client_id_file),
                                        ("--customer", args.customer), ("--out", args.out)) if not value]
    if missing:
        raise lc.Refusal("Missing %s. %s" % (", ".join(missing), ASK))
    refuse_secret("--project-id", args.project_id)
    if not re.match(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$", args.project_id):
        raise lc.Refusal("I can't read %s as a Google Cloud project ID. It is 6 to 30 lowercase letters, digits and dashes, "
                         "starting with a letter. The Cloud console shows it on the project's dashboard." % args.project_id)
    customer = lc.customer_id(args.customer)
    login = lc.customer_id(args.login_customer, "the manager account ID") if args.login_customer else None
    credentials = safe_path("--credentials-path", args.credentials_path) or default_credentials_path()
    client_file = safe_path("--client-id-file", args.client_id_file)
    out = os.path.abspath(args.out)
    work = safe_path("--work", args.work) or os.path.join(out, "work")
    os.makedirs(out, exist_ok=True)
    config_path = os.path.join(out, "tools_config.yaml")
    entry = server_entry(args.project_id, credentials, config_path, login)
    files = {"tools_config.yaml": tools_config(),
             "mcp-server.json": json.dumps({"mcpServers": {"google-ads": entry}}, indent=2) + "\n",
             "mcp-server.toml": toml(entry),
             "setup-checklist.md": checklist(args.project_id, credentials, config_path, client_file, login, customer, work, entry)}
    home = os.path.expanduser("~")
    for name, text in files.items():
        if args.as_home and home not in ("", "/"):
            text = text.replace(home, args.as_home)
            files[name] = text
        with open(os.path.join(out, name), "w", encoding="utf-8") as handle:
            handle.write(text)
    print("Wrote the setup files to %s: tools_config.yaml (read only), mcp-server.json, mcp-server.toml and setup-checklist.md." % out)
    print("No secret was asked for or written. The person runs the sign in themselves.")
    print("Send the person the whole checklist below. They do it in order and come back at the two checkpoints.\n")
    print(files["setup-checklist.md"])


if __name__ == "__main__":
    main()
