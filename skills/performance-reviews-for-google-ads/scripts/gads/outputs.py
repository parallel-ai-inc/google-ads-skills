"""Small writers shared by the skills: CSV, Markdown tables, Editor files."""
import csv
import json
import os

from .negatives import list_form

# Google Ads Editor reads these headers (English, any capitalisation).
EDITOR_NEGATIVE_HEADER = ["Campaign", "Ad Group", "Keyword", "Criterion Type"]


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, ensure_ascii=False)
    return path


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def md_table(header, rows):
    def clean(value):
        return str("" if value is None else value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(clean(h) for h in header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(clean(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def editor_criterion_type(match_type, level):
    """'phrase', 'campaign' -> 'Campaign Negative Phrase'."""
    label = "Negative %s" % match_type.capitalize()
    return "Campaign " + label if level == "campaign" else label


def write_editor_negatives(path, negatives):
    """Negative keywords as a Google Ads Editor import file.

    Campaign and ad group negatives only. Editor's CSV has no documented column
    for account level negative keyword lists, so those are written to a plain
    list by write_account_list instead.
    """
    rows = []
    for neg in negatives:
        if neg.get("level") == "account":
            continue
        ad_group = neg.get("ad_group", "") if neg.get("level") == "ad_group" else ""
        rows.append([neg.get("campaign", ""), ad_group, neg["text"], editor_criterion_type(neg["match"], neg.get("level", "campaign"))])
    return write_csv(path, EDITOR_NEGATIVE_HEADER, rows), len(rows)


def write_account_list(path, negatives):
    """Account level negatives, one per line, as they are typed into a negative
    keyword list in Google Ads: word for broad, "a phrase" for phrase, [exact]."""
    lines = [list_form(n["text"], n["match"]) for n in negatives if n.get("level") == "account"]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + ("\n" if lines else ""))
    return path, len(lines)
