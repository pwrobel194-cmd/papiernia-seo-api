"""Read-only snapshot of Communion SEO target pages via existing API v3.
No POST/PUT/PATCH/DELETE. No write to store. No secrets logged.
"""
import hashlib
import json
import os
import pathlib
import re
import requests

BASE = "https://papiernia.net.pl/papiernia-seo-api"
TARGETS = [
    ("category", "https://papiernia.net.pl/komunia"),
    ("product", "https://papiernia.net.pl/podziekowania-dla-gosci-komunia-swieczka"),
    ("product", "https://papiernia.net.pl/pamiatki-po-komunii-dla-gosci-slodkie-podziekowania-komunijne"),
]
KEY = os.environ.get("PAPIERNIA_SEO_API_KEY")
if not KEY:
    raise RuntimeError("Secret missing; no authenticated requests attempted.")
s = requests.Session()
s.headers.update({"X-Papiernia-SEO-Key": KEY, "Accept": "application/json"})
out = pathlib.Path("audit/komunia-20261108")
out.mkdir(parents=True, exist_ok=True)

def get(path, params=None):
    response = s.get(BASE + path, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def val(record, name):
    for k in (name, name[0].upper() + name[1:]):
        if k in record:
            return record[k]
    return None

def main():
    report=[]
    for typ,url in TARGETS:
        resolved=get("/v1/Resolve", {"url":url})
        eid=val(resolved,"id")
        entity=val(resolved,"entity")
        if not isinstance(eid,int) and not (isinstance(eid,str) and eid.isdecimal()):
            raise RuntimeError("Cannot resolve entity id for " + url)
        if str(entity).lower()!=typ:
            raise RuntimeError("Unexpected entity type for " + url)
        eid=int(eid)
        endpoint=("CategorySnapshot" if typ=="category" else "ProductSnapshot")
        raw=get(f"/v3/{endpoint}/{eid}")
        # Read-only release data; use only public SEO fields, never private keys/settings.
        current=raw.get("data",raw.get("snapshot",raw))
        if not isinstance(current,dict):
            raise RuntimeError("Unexpected API shape " + url)
        desc_field="description" if typ=="category" else "fullDescription"
        fields=["name","metaTitle","metaDescription","metaKeywords","seName",desc_field]
        if typ=="product":fields.append("shortDescription")
        fields_data={f:val(current,f) for f in fields}
        if fields_data["name"] is None:
            raise RuntimeError("Name field missing " + url + "; keys=" + ",".join(sorted(current.keys())))
        html=fields_data.get(desc_field) or ""
        imgs=re.findall(r"<img\\b[^>]*>",html,re.I)
        links=re.findall(r"<a\\b[^>]*>",html,re.I)
        row={"type":typ,"id":eid,"url":url,"fields":fields_data,
             "html_sha256":hashlib.sha256(html.encode("utf-8")).hexdigest(),
             "html_length":len(html),"html_images":imgs,"html_links":links}
        report.append(row)
        print(json.dumps({"type":typ,"id":eid,"url":url,"name":fields_data["name"],
          "metaTitle":fields_data["metaTitle"],"metaDescription":fields_data["metaDescription"],
          "html_length":len(html),"image_count":len(imgs),"link_count":len(links),
          "html_sha256":row["html_sha256"]}, ensure_ascii=False))
    (out/"readonly-snapshots.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__ == "__main__":
    main()
