"""Write a Word document (.docx) with the standard library only.

A .docx is a zip of XML files, like the workbook writer in gads/xlsx.py.
Enough for a client report: a title, headings, paragraphs with **bold**
words, bullet lists and simple tables with a shaded header row.
"""
import datetime as dt
import re
import zipfile
from xml.sax.saxutils import escape

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
PAGE_WIDTH, MARGIN = 12240, 1080
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""

_BORDER = '<w:%s w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles %s>
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="60"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:color w:val="595959"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:numPr><w:numId w:val="1"/></w:numPr><w:spacing w:after="60"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Small"><w:name w:val="Small"/><w:basedOn w:val="Normal"/><w:qFormat/><w:rPr><w:color w:val="595959"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:style>
<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>
<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:basedOn w:val="TableNormal"/><w:tblPr><w:tblBorders>%s</w:tblBorders></w:tblPr></w:style>
</w:styles>""" % (NS, "".join(_BORDER % side for side in ("top", "left", "bottom", "right", "insideH", "insideV")))

_NUMBERING = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering %s><w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum><w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>""" % NS

_CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>%s</dc:title><dc:creator>%s</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created></cp:coreProperties>"""

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _text(value):
    return escape(_CONTROL.sub("", str(value)))


def _runs(text, size=None, bold=False):
    """Text to runs. **word** becomes bold."""
    out = []
    for index, part in enumerate(re.split(r"\*\*", str(text))):
        if not part:
            continue
        props = ("<w:b/>" if bold or index % 2 else "") + ('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size) if size else "")
        out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % ("<w:rPr>%s</w:rPr>" % props if props else "", _text(part)))
    return "".join(out)


class Document:
    def __init__(self):
        self._body = []

    def _paragraph(self, text, style=None, extra=""):
        props = ('<w:pStyle w:val="%s"/>' % style if style else "") + extra
        self._body.append("<w:p>%s%s</w:p>" % ("<w:pPr>%s</w:pPr>" % props if props else "", _runs(text)))

    def title(self, text):
        self._paragraph(text, "Title")

    def subtitle(self, text):
        self._paragraph(text, "Subtitle")

    def heading(self, text, level=1):
        self._paragraph(text, "Heading%d" % level)

    def paragraph(self, text):
        self._paragraph(text)

    def small(self, text):
        self._paragraph(text, "Small")

    def bullet(self, text):
        self._paragraph(text, "ListBullet")

    def table(self, header, rows, numeric=()):
        """numeric: column indexes to align right."""
        count = len(header)
        weights = [2.4] + [1.0] * (count - 1)
        widths = [int(TEXT_WIDTH * w / sum(weights)) for w in weights]
        size = 16 if count > 7 else 18

        def cell(value, width, column, head=False):
            align = '<w:jc w:val="right"/>' if column in numeric and column else ""
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="EDEDED"/>' if head else ""
            return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr><w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>%s</w:pPr>%s</w:p></w:tc>'
                    % (width, shade, align, _runs("" if value is None else value, size=size, bold=head)))

        out = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
               '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>' % sum(widths),
               "<w:tblGrid>%s</w:tblGrid>" % "".join('<w:gridCol w:w="%d"/>' % w for w in widths),
               "<w:tr><w:trPr><w:tblHeader/></w:trPr>%s</w:tr>" % "".join(cell(h, widths[i], i, True) for i, h in enumerate(header))]
        for row in rows:
            out.append("<w:tr>%s</w:tr>" % "".join(cell(row[i] if i < len(row) else "", widths[i], i) for i in range(count)))
        out.append("</w:tbl>")
        self._body.append("".join(out))
        self._paragraph("", extra='<w:spacing w:after="60"/>')

    def save(self, path, title="", author=""):
        document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document %s><w:body>%s'
                    '<w:sectPr><w:pgSz w:w="%d" w:h="15840"/><w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
                    "</w:body></w:document>" % (NS, "".join(self._body), PAGE_WIDTH, MARGIN, MARGIN, MARGIN, MARGIN))
        created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
            archive.writestr("_rels/.rels", _RELS)
            archive.writestr("word/document.xml", document)
            archive.writestr("word/_rels/document.xml.rels", _DOC_RELS)
            archive.writestr("word/styles.xml", _STYLES)
            archive.writestr("word/numbering.xml", _NUMBERING)
            archive.writestr("docProps/core.xml", _CORE % (_text(title), _text(author), created))
        return path
