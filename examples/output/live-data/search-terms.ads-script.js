/**
 * Search terms report: a read only report, written to a Google Sheet you own.
 *
 * It reads this account and writes one tab of the Sheet, in the layout of a
 * Google Ads download: the report name, the date range, the header, the rows
 * and a total row. It makes no change to the account. It calls only
 * AdsApp.search to read, and SpreadsheetApp to write the Sheet.
 *
 * Written to Google's documented Ads scripts API. Not yet run in an account:
 * press Preview first, read the log, then schedule it.
 */
var SHEET_URL = 'PASTE_YOUR_SHEET_URL_HERE';
var TAB_NAME = 'Search terms report';
var DAYS = 30;
var REPORT = {
  "title": "Search terms report",
  "resource": "search_term_view",
  "fields": [
    "search_term_view.search_term",
    "segments.search_term_match_type",
    "search_term_view.status",
    "campaign.name",
    "ad_group.name",
    "campaign.advertising_channel_type",
    "metrics.impressions",
    "metrics.clicks",
    "metrics.ctr",
    "metrics.average_cpc",
    "metrics.cost_micros",
    "metrics.conversions",
    "metrics.cost_per_conversion",
    "metrics.conversions_value"
  ],
  "conditions": [],
  "orderings": [
    "metrics.cost_micros DESC"
  ],
  "total": "Total: Search terms",
  "currencyAt": 6,
  "columns": [
    {
      "header": "Search term",
      "field": "search_term_view.search_term",
      "kind": "text"
    },
    {
      "header": "Match type",
      "field": "segments.search_term_match_type",
      "kind": "enum"
    },
    {
      "header": "Added/Excluded",
      "field": "search_term_view.status",
      "kind": "enum"
    },
    {
      "header": "Campaign",
      "field": "campaign.name",
      "kind": "text"
    },
    {
      "header": "Ad group",
      "field": "ad_group.name",
      "kind": "text"
    },
    {
      "header": "Campaign type",
      "field": "campaign.advertising_channel_type",
      "kind": "enum"
    },
    {
      "header": "Impr.",
      "field": "metrics.impressions",
      "kind": "int",
      "sum": true
    },
    {
      "header": "Clicks",
      "field": "metrics.clicks",
      "kind": "int",
      "sum": true
    },
    {
      "header": "CTR",
      "field": "metrics.ctr",
      "kind": "percent"
    },
    {
      "header": "Avg. CPC",
      "field": "metrics.average_cpc",
      "kind": "micros"
    },
    {
      "header": "Cost",
      "field": "metrics.cost_micros",
      "kind": "micros",
      "sum": true
    },
    {
      "header": "Conversions",
      "field": "metrics.conversions",
      "kind": "decimal",
      "sum": true
    },
    {
      "header": "Cost / conv.",
      "field": "metrics.cost_per_conversion",
      "kind": "micros"
    },
    {
      "header": "Conv. value",
      "field": "metrics.conversions_value",
      "kind": "decimal",
      "sum": true
    }
  ],
  "enums": {
    "segments.search_term_match_type": {
      "BROAD": "Broad match",
      "EXACT": "Exact match",
      "PHRASE": "Phrase match",
      "NEAR_EXACT": "Exact match (close variant)",
      "NEAR_PHRASE": "Phrase match (close variant)"
    },
    "search_term_view.status": {
      "ADDED": "Added",
      "EXCLUDED": "Excluded",
      "ADDED_EXCLUDED": "Added/Excluded",
      "NONE": "None"
    },
    "campaign.advertising_channel_type": {
      "SEARCH": "Search",
      "DISPLAY": "Display",
      "SHOPPING": "Shopping",
      "VIDEO": "Video",
      "MULTI_CHANNEL": "App",
      "PERFORMANCE_MAX": "Performance Max",
      "DEMAND_GEN": "Demand Gen",
      "LOCAL": "Local",
      "SMART": "Smart",
      "HOTEL": "Hotel",
      "LOCAL_SERVICES": "Local services",
      "TRAVEL": "Travel"
    }
  }
};
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
