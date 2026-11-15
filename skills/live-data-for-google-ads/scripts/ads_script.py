#!/usr/bin/env python3
"""Write a read only Google Ads script for one named report. The person pastes
it into their own account and schedules it. Each run writes the report to a
tab of a Google Sheet they own, in the layout of a Google Ads download, and
changes nothing in the account.

    python3 scripts/ads_script.py REPORT --out OUTPUT [--sheet-url URL] [--days 30]
    python3 scripts/ads_script.py --list

Written to Google's documented Ads scripts API (AdsApp.search, SpreadsheetApp).
Not yet run in an account: the person previews it before scheduling it.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livecore as lc  # noqa: E402

SUPPORTED = ("search-terms", "keywords", "campaigns", "campaigns-by-day", "ad-groups", "ads", "conversions-by-action-and-day")
SCRIPT_KINDS = ("text", "int", "micros", "decimal", "percent", "share", "lost", "enum", "keyword", "parents", "ad_name", "first")
# Every method the scripts call. A test holds the scripts to this list, so a write call cannot slip in.
ALLOWED_CALLS = ("currentAccount", "getTimeZone", "getCurrencyCode", "formatDate", "search", "hasNext", "next", "push",
                 "openByUrl", "getSheetByName", "insertSheet", "clearContents", "getRange", "setValues", "join", "slice",
                 "map", "split", "replace", "toUpperCase", "toLowerCase", "charAt", "substring", "indexOf", "toFixed",
                 "concat", "getTime", "now", "abs", "round", "log", "hasOwnProperty", "isArray", "splice")

TEMPLATE = r"""/**
 * __TITLE__: a read only report, written to a Google Sheet you own.
 *
 * It reads this account and writes one tab of the Sheet, in the layout of a
 * Google Ads download: the report name, the date range, the header, the rows
 * and a total row. It makes no change to the account. It calls only
 * AdsApp.search to read, and SpreadsheetApp to write the Sheet.
 *
 * Written to Google's documented Ads scripts API. Not yet run in an account:
 * press Preview first, read the log, then schedule it.
 */
var SHEET_URL = '__SHEET__';
var TAB_NAME = '__TAB__';
var DAYS = __DAYS__;
var REPORT = __SPEC__;
var EMPTY = '--';
var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function main() {
  if (SHEET_URL.indexOf('https://docs.google.com/spreadsheets/') !== 0) {
    throw new Error('Paste the address of a Google Sheet you own into SHEET_URL first.');
  }
  var account = AdsApp.currentAccount();
  var zone = account.getTimeZone();
  var day = 24 * 3600 * 1000;
  var end = new Date(Date.now() - day);
  var start = new Date(end.getTime() - (DAYS - 1) * day);
  var conditions = REPORT.conditions.slice();
  conditions.push("segments.date BETWEEN '" + Utilities.formatDate(start, zone, 'yyyy-MM-dd') + "' AND '" +
                  Utilities.formatDate(end, zone, 'yyyy-MM-dd') + "'");
  var query = 'SELECT ' + REPORT.fields.join(', ') + ' FROM ' + REPORT.resource + ' WHERE ' + conditions.join(' AND ');
  if (REPORT.orderings.length) {
    query += ' ORDER BY ' + REPORT.orderings.join(', ');
  }
  var header = REPORT.columns.map(function (column) { return column.header; });
  header.splice(REPORT.currencyAt, 0, 'Currency code');
  var currency = account.getCurrencyCode();
  var sums = {};
  var body = [];
  var rows = AdsApp.search(query);
  while (rows.hasNext()) {
    var row = rows.next();
    var line = REPORT.columns.map(function (column) { return cell(row, column, sums); });
    line.splice(REPORT.currencyAt, 0, currency);
    body.push(line);
  }
  var total = REPORT.columns.map(function (column, index) {
    if (index === 0) { return REPORT.total; }
    return column.sum ? round2(sums[column.header] || 0) : EMPTY;
  });
  total.splice(REPORT.currencyAt, 0, currency);
  var range = longDate(start, zone) + ' - ' + longDate(end, zone);
  var grid = [[REPORT.title], [range], header].concat(body).concat([total]);
  var width = header.length;
  grid = grid.map(function (line) {
    var padded = line.slice();
    while (padded.length < width) { padded.push(''); }
    return padded;
  });
  var book = SpreadsheetApp.openByUrl(SHEET_URL);
  var tab = book.getSheetByName(TAB_NAME) || book.insertSheet(TAB_NAME);
  tab.clearContents();
  tab.getRange(1, 1, grid.length, width).setValues(grid);
  Logger.log('Wrote ' + body.length + ' rows to the tab ' + TAB_NAME + '. The account was not changed.');
}

function longDate(date, zone) {
  var parts = Utilities.formatDate(date, zone, 'yyyy-M-d').split('-');
  return MONTHS[Number(parts[1]) - 1] + ' ' + parts[2] + ', ' + parts[0];
}

function camel(part) {
  return part.replace(/_([a-z0-9])/g, function (whole, letter) { return letter.toUpperCase(); });
}

function pick(row, path) {
  var value = row;
  var parts = path.split('.');
  for (var i = 0; i < parts.length; i++) {
    if (value === null || value === undefined) { return null; }
    value = value[camel(parts[i])];
  }
  return value === undefined ? null : value;
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function words(field, value) {
  if (value === null || value === '' || value === 'UNSPECIFIED' || value === 'UNKNOWN') { return EMPTY; }
  var known = REPORT.enums[field];
  if (known && known.hasOwnProperty(value)) { return known[value]; }
  var text = String(value).replace(/_/g, ' ').toLowerCase();
  return text.charAt(0).toUpperCase() + text.substring(1);
}

function percent(ratio) {
  return (ratio * 100).toFixed(2) + '%';
}

function cell(row, column, sums) {
  var value = pick(row, column.field);
  var kind = column.kind;
  if (kind === 'int' || kind === 'micros' || kind === 'decimal') {
    var amount = value === null ? (column.field.indexOf('metrics.') === 0 ? 0 : null) : Number(value);
    if (amount === null) { return EMPTY; }
    if (kind === 'micros') { amount = amount / 1000000; }
    if (column.sum) { sums[column.header] = (sums[column.header] || 0) + amount; }
    return kind === 'int' ? Math.round(amount) : round2(amount);
  }
  if (kind === 'percent' || kind === 'share' || kind === 'lost') {
    if (value === null) { return EMPTY; }
    var ratio = Number(value);
    if (kind === 'share' && Math.abs(ratio - 0.0999) < 1e-9) { return '< 10%'; }
    if (kind === 'lost' && Math.abs(ratio - 0.9001) < 1e-9) { return '> 90%'; }
    return percent(ratio);
  }
  if (kind === 'enum') { return words(column.field, value); }
  if (kind === 'keyword') {
    var match = pick(row, column.inputs[0]);
    if (!value) { return EMPTY; }
    return match === 'EXACT' ? '[' + value + ']' : (match === 'PHRASE' ? '"' + value + '"' : value);
  }
  if (kind === 'parents') {
    var fields = [column.field].concat(column.inputs || []);
    for (var i = 0; i < fields.length; i++) {
      var state = pick(row, fields[i]);
      if (state === 'PAUSED' || state === 'REMOVED') {
        return (fields[i] === 'campaign.status' ? 'Campaign ' : 'Ad group ') + state.toLowerCase();
      }
    }
    return EMPTY;
  }
  if (kind === 'ad_name') {
    if (Array.isArray(value) && value.length && value[0].text) { return value[0].text; }
    return pick(row, column.inputs[0]) || ('Ad ID ' + pick(row, column.inputs[1]));
  }
  if (kind === 'first') {
    return Array.isArray(value) && value.length ? value[0] : (value || EMPTY);
  }
  return value === null || value === '' ? EMPTY : value;
}
"""


def spec_for(name, days):
    spec = lc.REPORTS[name]
    for column in spec["columns"]:
        if column["kind"] not in SCRIPT_KINDS:
            raise lc.Refusal("The report %s has a column a script cannot write yet." % name)
    fields = lc.report_fields(spec)
    lc.check_fields(lc.Catalogue(), spec["resource"], fields, [c for c in spec["conditions"] if not c.startswith("{")], spec["orderings"])
    currency_at = next((i for i, c in enumerate(spec["columns"]) if c["kind"] in ("int", "micros", "decimal", "percent", "share", "lost")),
                       len(spec["columns"]))
    return {"title": spec["title"], "resource": spec["resource"], "fields": fields,
            "conditions": [c for c in spec["conditions"] if not c.startswith("{")], "orderings": spec["orderings"],
            "total": spec["total"], "currencyAt": currency_at,
            "columns": [{k: v for k, v in c.items() if k in ("header", "field", "kind", "inputs", "sum")} for c in spec["columns"]],
            "enums": {c["field"]: lc.ENUMS[c["field"]] for c in spec["columns"] if c["kind"] == "enum" and c["field"] in lc.ENUMS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", nargs="?", help="a named report: " + ", ".join(SUPPORTED))
    parser.add_argument("--out", help="folder for the script")
    parser.add_argument("--sheet-url", default="", help="the address of a Google Sheet the person owns")
    parser.add_argument("--days", type=int, help="days to read, ending yesterday. Default: the report's own")
    parser.add_argument("--list", action="store_true", help="the reports a script can write")
    args = parser.parse_args()
    if args.list or not args.report:
        print("Reports a script can write: %s." % ", ".join(SUPPORTED))
        print("Change history and the conversion actions summary need two searches, so they are left to the live search and to downloads.")
        return
    if args.report not in SUPPORTED:
        raise lc.Refusal("A script cannot write %s. Pick one of: %s." % (args.report, ", ".join(SUPPORTED)))
    if not args.out:
        raise lc.Refusal("Give --out, the folder for the script.")
    url = args.sheet_url.strip()
    if url and not re.match(r"^https://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-#=?&/.]*)?$", url):
        raise lc.Refusal("That is not a Google Sheets address. It starts with https://docs.google.com/spreadsheets/d/")
    days = args.days or lc.REPORTS[args.report]["days"]
    if not 1 <= days <= 400:
        raise lc.Refusal("Pick between 1 and 400 days.")
    spec = spec_for(args.report, days)
    text = (TEMPLATE.replace("__TITLE__", spec["title"]).replace("__SHEET__", url or "PASTE_YOUR_SHEET_URL_HERE")
            .replace("__TAB__", spec["title"] if args.report != "campaigns-by-day" else "Campaigns by day")
            .replace("__DAYS__", str(days)).replace("__SPEC__", json.dumps(spec, indent=2)))
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "%s.ads-script.js" % args.report)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("Wrote %s: %s for the last %d full days, to the tab \"%s\"." % (path, spec["title"], days,
                                                                            "Campaigns by day" if args.report == "campaigns-by-day" else spec["title"]))
    print("It reads with AdsApp.search and writes only to the Sheet. It makes no change to the account.")
    print("Written to Google's documented Ads scripts API and not yet run in an account: press Preview before scheduling it.")
    if not url:
        print("Paste the address of a Google Sheet you own into SHEET_URL at the top of the script.")
    print("\nIn Google Ads: Tools, Bulk actions, Scripts, then the plus button. Paste the script, authorize it, press Preview and read the log. "
          "Then set its frequency, such as daily. Download the tab as CSV to give it to another skill in this pack.")


if __name__ == "__main__":
    main()
