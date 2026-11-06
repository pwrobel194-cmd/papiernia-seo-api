#!/usr/bin/env python3
"""Read-only snapshots of 38 products and previews of 9 names. No live writes."""
import json
import os
import re
import sys
from pathlib import Path
import requests

BASE="https://papiernia.net.pl/papiernia-seo-api"
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY")
if not KEY: raise SystemExit("API key unavailable - no requests sent")
C=requests.Session()
C.headers.update({"X-Papiernia-SEO-Key":KEY,"Accept":"application/json"})
PLAN=Path("automation/christmas-h1-intents-20261106.json")
REPORT=Path("reports/christmas-h1-preview-20261106.json")

def val(obj,name,default=None):
    return obj.get(name,obj.get(name[0].lower()+name[1:],default))

def api(method,path,**kw):
    if method not in ("GET","POST"): raise RuntimeError("Read-only and Preview-only")
    if method=="POST" and not re.fullmatch(r"/v3/PreviewProductSeo/[0-9]+",path):
        raise RuntimeError("Only PreviewProductSeo POST permitted")
    r=C.request(method,BASE+path,timeout=45,**kw)
    if not r.ok: raise RuntimeError("HTTP "+str(r.status_code)+" on "+path)
    return r.json()

def compact(s):
    return {"name":val(s,"Name"),"slug":val(s,"Slug",val(s,"SeName")),
            "metaTitle":val(s,"MetaTitle"),"published":val(s,"Published"),
            "deleted":val(s,"Deleted"),"updatedOnUtc":val(s,"UpdatedOnUtc"),
            "shortDescriptionLength":len(val(s,"ShortDescription") or ""),
            "fullDescriptionLength":len(val(s,"FullDescription") or "")}

def save(report):
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    p=json.loads(PLAN.read_text(encoding="utf-8"))
    items=p["products"]
    assert len(items)==38 and len({x["slug"] for x in items})==38
    health=api("GET","/v1/Health")
    if val(health,"Ok") is not True: raise RuntimeError("API health is not OK")
    report={"scope":"PREVIEW ONLY - no commit, no slug changes",
            "rules":p["rules"],"entries":[],"summary":{"read":0,"preview":0,"error":0}}
    for item in items:
        slug=item["slug"]; mode=item["mode"]; proposed=item["proposedName"]
        line={"slug":slug,"url":"https://papiernia.net.pl/"+slug,
              "mode":mode,"proposedName":proposed}
        try:
            resolved=api("GET","/v1/Resolve",params={"url":line["url"]})
            if str(val(resolved,"Entity")).lower()!="product":
                raise RuntimeError("Wrong entity type")
            pid=int(val(resolved,"Id"))
            snap=api("GET","/v3/ProductSnapshot/"+str(pid))
            before=compact(snap)
            if before["slug"]!=slug or before["deleted"] is True or before["published"] is not True:
                raise RuntimeError("SAFETY: unexpected slug or status")
            line.update({"productId":pid,"before":before})
            report["summary"]["read"]+=1
            if mode=="preview" and before["name"]!=proposed:
                payload={"name":proposed,"reason":"Preview only: SEO intencje bez zmiany slug"}
                preview=api("POST","/v3/PreviewProductSeo/"+str(pid),json=payload)
                after=val(preview,"After",{})
                new_slug=val(after,"Slug",val(after,"SeName"))
                if val(preview,"DryRun") is not True or not val(preview,"ApprovalToken"):
                    raise RuntimeError("Preview not approved by API")
                if val(after,"Name")!=proposed or new_slug not in (None,slug):
                    raise RuntimeError("SAFETY: mismatch or slug change in preview")
                if compact(api("GET","/v3/ProductSnapshot/"+str(pid)))!=before:
                    raise RuntimeError("SAFETY: preview mutated product")
                line["status"]="PREVIEW_OK_NO_WRITE"
                line["previewSlug"]=new_slug or slug
                report["summary"]["preview"]+=1
            else:
                line["status"]="ALREADY_MATCHES" if mode=="preview" else "REVIEW_ONLY"
        except Exception as e:
            line["status"]="ERROR"
            line["error"]=str(e)
            report["summary"]["error"]+=1
        report["entries"].append(line)
        save(report)
        print(json.dumps({"slug":slug,"mode":mode,"status":line["status"]},ensure_ascii=False),flush=True)
    print("SUMMARY "+json.dumps(report["summary"]),flush=True)
    return 1 if report["summary"]["error"] else 0

if __name__=="__main__":
    sys.exit(main())
