"""Write a real .xlsx workbook with the standard library only.

Enough for professional deliverables: several sheets, a bold frozen header
row, column widths, and number formats for whole numbers, money and percent.
"""
import re
import zipfile
from xml.sax.saxutils import escape

# Style ids defined in _STYLES below.
STYLE = {"text": 0, "header": 1, "int": 2, "money": 3, "pct": 4, "wrap": 5}

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
%s</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="2"><numFmt numFmtId="164" formatCode="#,##0.00"/><numFmt numFmtId="165" formatCode="0.0%"/></numFmts>
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFEDEDED"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="6">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="3" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
</cellXfs>
</styleSheet>"""

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _column(index):
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _safe_text(value):
    text = _CONTROL.sub("", str(value))
    # A cell that starts with = + - @ is shown as text, never run as a formula.
    return escape(text)


class Workbook:
    def __init__(self):
        self._sheets = []

    def add_sheet(self, name, header, rows, formats=None, widths=None):
        """formats: {column index: 'int' | 'money' | 'pct' | 'wrap'}."""
        name = re.sub(r"[\[\]:*?/\\]", " ", name)[:31]
        self._sheets.append((name, list(header), [list(r) for r in rows], formats or {}, widths or {}))

    def _sheet_xml(self, header, rows, formats, widths):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
               '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
               "<cols>"]
        for index in range(len(header)):
            longest = max([len(str(header[index]))] + [len(str(r[index])) for r in rows[:200] if index < len(r) and r[index] is not None] or [8])
            width = widths.get(index, min(max(longest + 2, 9), 60))
            out.append('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (index + 1, index + 1, width))
        out.append("</cols><sheetData>")

        def cell(ref, value, style):
            if value is None or value == "":
                return ""
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            if isinstance(value, (int, float)):
                return '<c r="%s" s="%d"><v>%s</v></c>' % (ref, style, repr(float(value)) if isinstance(value, float) else value)
            return '<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, style, _safe_text(value))

        out.append('<row r="1">' + "".join(cell("%s1" % _column(i), h, STYLE["header"]) for i, h in enumerate(header)) + "</row>")
        for number, row in enumerate(rows, start=2):
            cells = []
            for index, value in enumerate(row):
                kind = formats.get(index, "text")
                style = STYLE[kind] if isinstance(value, (int, float)) and not isinstance(value, bool) or kind == "wrap" else STYLE["text"]
                cells.append(cell("%s%d" % (_column(index), number), value, style))
            out.append('<row r="%d">%s</row>' % (number, "".join(cells)))
        out.append("</sheetData></worksheet>")
        return "".join(out)

    def save(self, path):
        overrides, sheet_tags, rel_tags = [], [], []
        for number, (name, _, _, _, _) in enumerate(self._sheets, start=1):
            overrides.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % number)
            sheet_tags.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(name, {'"': "&quot;"}), number, number))
            rel_tags.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (number, number))
        style_rel = len(self._sheets) + 1
        workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    "<sheets>%s</sheets></workbook>" % "".join(sheet_tags))
        workbook_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s'
                         '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                         "</Relationships>" % ("".join(rel_tags), style_rel))
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", _CONTENT_TYPES % "".join(overrides))
            archive.writestr("_rels/.rels", _RELS)
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
            archive.writestr("xl/styles.xml", _STYLES)
            for number, (_, header, rows, formats, widths) in enumerate(self._sheets, start=1):
                archive.writestr("xl/worksheets/sheet%d.xml" % number, self._sheet_xml(header, rows, formats, widths))
        return path
