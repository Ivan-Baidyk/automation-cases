#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, io, json, urllib.request, urllib.error, zipfile

BASE = "http://localhost:4000"

def make_docx(text):
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', document)
    return buf.getvalue()

def req(path, body=None, method=None):
    headers = {"carbone-version": "5", "Content-Type": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data, headers=headers,
                               method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

s, b, _ = req("/status")
print("STATUS:", s, b.decode())

docx = make_docx("Hello {d.name} from {d.company}")
b64 = base64.b64encode(docx).decode()
print("DOCX template bytes:", len(docx))

s, b, _ = req("/template", {"template": b64})
print("UPLOAD:", s, b.decode())
data = json.loads(b).get("data", {})
tid = data.get("templateId") or data.get("id") or data.get("versionId")
print("templateId:", tid)

s, b, _ = req("/render/" + tid, {"data": {"name": "Ivan Baidyk", "company": "AiMentorCRM"}})
print("RENDER DOCX:", s, b.decode())
rid = json.loads(b)["data"]["renderId"]

s, b, _ = req("/render/" + rid)
open("/opt/carbone/test-output.docx", "wb").write(b)
print("DOWNLOAD DOCX:", s, "bytes:", len(b))
with zipfile.ZipFile(io.BytesIO(b)) as z:
    inner = z.read("word/document.xml").decode("utf-8", "ignore")
print("DOCX has Ivan Baidyk:", "Ivan Baidyk" in inner, "| still placeholder:", "{d.name}" in inner)

s, b, _ = req("/render/" + tid, {"data": {"name": "Ivan Baidyk", "company": "AiMentorCRM"}, "convertTo": "pdf"})
print("RENDER PDF:", s, b.decode())
rid2 = json.loads(b)["data"]["renderId"]
s, b, _ = req("/render/" + rid2)
open("/opt/carbone/test-output.pdf", "wb").write(b)
print("DOWNLOAD PDF:", s, "bytes:", len(b), "| PDF magic ok:", b[:5] == b"%PDF-")

print("DONE")
