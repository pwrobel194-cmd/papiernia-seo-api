#!/usr/bin/env python3
"""Owner-approved Christmas SEO deployment, 14 Nov 2026.
API v3 preview -> commit -> readback, 5 existing products.
Only MetaTitle and MetaDescription may change.
Never change H1, slugs, HTML, images, category, stock or price.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://papiernia.net.pl"
API=BASE+"/papiernia-seo-api"
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY","")
if not KEY:
    raise RuntimeError("Existing GitHub Actions API secret missing")
s=requests.Session()
s.headers.update({"X-Papiernia-SEO-Key":KEY,"Accept":"application/json"})
OUT=Path("reports/christmas-five-20261114")
OUT.mkdir(parents=True,exist_ok=True)
REASON="Zatwierdzone przez właściciela 14.11.2026: dopasowanie meta SEO pięciu produktów świątecznych do intencji zakupowych, bez zmiany H1, URL i treści."
TARGETS=[
  {"slug":"magnesy-swiateczne","id":4917,"expectedName":"Magnesy świąteczne z logo firmy – prezent dla klientów",
   "metaTitle":"Magnesy świąteczne z logo dla klientów | Papiernia",
   "metaDescription":"Personalizowane magnesy świąteczne z logo firmy i życzeniami. Złoty karton typu lustro, woreczek do zapakowania. Zamów z nadrukiem od 30 sztuk."},
  {"slug":"swieczki-dla-pracownikow-upominek-swiateczny-dla-firm","id":4918,"expectedName":"Świeczka serce w EKO opakowaniu – upominek dla pracowników",
   "metaTitle":"Świeczki świąteczne dla pracowników z logo | Papiernia",
   "metaDescription":"Białe świeczki serca w opakowaniu EKO z etykietą i logo firmy. Drobne podziękowania świąteczne dla pracowników z personalizacją od 30 sztuk."},
  {"slug":"tani-upominek-dla-klientow-na-swieta","id":4946,"expectedName":"Tanie podziękowanie dla klientek na święta – ciasteczko z wróżbą",
   "metaTitle":"Ciasteczko z wróżbą na Święta z logo | Papiernia",
   "metaDescription":"Ciasteczko z wróżbą na Święta dla klientek z personalizowaną etykietą 4 cm. Bez pudełeczka, etykieta do samodzielnego naklejenia. Zamów od 30 sztuk."},
  {"slug":"notesy-swiateczne-upominki-swiateczne","id":4921,"expectedName":"Notesiki świąteczne z logo – upominek firmowy dla klientów",
   "metaTitle":"Notesiki świąteczne z logo i ołówkiem | Papiernia",
   "metaDescription":"Mini notesiki świąteczne z 25 kartkami, ołówkiem i personalizowanym bilecikiem z logo firmy. Drobny prezent dla klientów i pracowników. Od 30 sztuk."},
  {"slug":"lizaki-reklamowe-z-nadrukiem-logo-upominek-na-swieta","id":4952,"expectedName":"Lizak świąteczny z logo – upominek dla klientek salonu",
   "metaTitle":"Lizaki reklamowe z logo dla salonów na Święta | Papiernia",
   "metaDescription":"Biało-czerwone lizaki z logo i personalizowaną etykietą dla klientek salonów kosmetycznych i fryzjerskich na Boże Narodzenie. Zamów od 30 sztuk."}
]
def val(obj,name,default=None):
    return obj.get(name,obj.get(name[0].lower()+name[1:],default)) if isinstance(obj,dict) else default
def request(method,endpoint,**kw):
    r=s.request(method,API+endpoint,timeout=45,**kw)
    if r.status_code>=400:
        raise RuntimeError("%s %s HTTP %s: %s"%(method,endpoint,r.status_code,r.text[:350]))
    return r.json()
def fetch(t):
    return request("GET","/v3/ProductSnapshot/"+str(t["id"]))
def immutable(x):
    return {key:val(x,key) for key in ("Name","Sku","Slug","ShortDescription","FullDescription","MetaKeywords","Published","Deleted","Pictures")}
def meta(x):
    return {key:val(x,key) for key in ("MetaTitle","MetaDescription")}
report={"dateUtc":datetime.now(timezone.utc).isoformat(),"mode":"owner-approved controlled production deployment",
        "fieldsAllowed":["MetaTitle","MetaDescription"],"status":"STARTED","items":[]}
def persist():
    (OUT/"deployment-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
def apply(t):
    slug=t["slug"]
    item={"slug":slug,"id":t["id"],"url":BASE+"/"+slug,"fieldsAllowed":["MetaTitle","MetaDescription"]}
    try:
        if not 25<=len(t["metaTitle"])<=70:
            raise RuntimeError("SEO title length out of bounds")
        if not 90<=len(t["metaDescription"])<=175:
            raise RuntimeError("Meta description length out of bounds")
        resolved=request("GET","/v1/Resolve",params={"url":item["url"]})
        if str(val(resolved,"Entity","")).lower()!="product" or int(val(resolved,"Id",-1))!=t["id"]:
            raise RuntimeError("URL resolves to another entity")
        before=fetch(t)
        if val(before,"Slug")!=slug or val(before,"Name")!=t["expectedName"]:
            raise RuntimeError("Different product name/slug; stop")
        if val(before,"Published") is not True or val(before,"Deleted"):
            raise RuntimeError("Product is not an active published listing")
        item["before"]=meta(before)
        item["nameUnchanged"]=val(before,"Name")
        (OUT/(slug+"-before.json")).write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding="utf-8")
        desired={"MetaTitle":t["metaTitle"],"MetaDescription":t["metaDescription"]}
        item["desired"]=desired
        if meta(before)==desired:
            item["status"]="NO_CHANGE_ALREADY_MATCHES"
            report["items"].append(item)
            persist()
            print("SEO_PRODUCT "+json.dumps({"slug":slug,"id":t["id"],"status":item["status"]},ensure_ascii=False),flush=True)
            return
        payload={"metaTitle":t["metaTitle"],"metaDescription":t["metaDescription"],"reason":REASON}
        preview=request("POST","/v3/PreviewProductSeo/"+str(t["id"]),json=payload)
        token=val(preview,"ApprovalToken")
        after_preview=val(preview,"After",{})
        if val(preview,"DryRun") is not True or not token:
            raise RuntimeError("Missing validated preview and approval token")
        if val(after_preview,"MetaTitle")!=t["metaTitle"] or val(after_preview,"MetaDescription")!=t["metaDescription"]:
            raise RuntimeError("Preview differs from approved metadata")
        for field in ("Name","Sku","ShortDescription","FullDescription","MetaKeywords"):
            if val(after_preview,field)!=val(before,field):
                raise RuntimeError("Unexpected preview modification of "+field)
        slug_preview=val(after_preview,"SeName",val(after_preview,"Slug"))
        if slug_preview!=slug:
            raise RuntimeError("Preview attempts to change URL")
        # Re-read immediately; the API token itself also checks a before-state fingerprint.
        fresh=fetch(t)
        if immutable(fresh)!=immutable(before) or meta(fresh)!=meta(before) or val(fresh,"UpdatedOnUtc")!=val(before,"UpdatedOnUtc"):
            raise RuntimeError("Concurrent edit detected; no commit")
        commit=request("PUT","/v3/CommitProductSeo/"+str(t["id"]),
                       json={**payload,"approvalToken":token})
        if val(commit,"Committed") is not True:
            raise RuntimeError("API did not confirm commit")
        readback=fetch(t)
        if meta(readback)!=desired:
            raise RuntimeError("After-save metadata mismatch")
        if immutable(readback)!=immutable(before):
            raise RuntimeError("After-save immutable fields changed unexpectedly")
        item["after"]=meta(readback)
        item["status"]="APPLIED_VERIFIED"
        print("SEO_PRODUCT "+json.dumps({"slug":slug,"id":t["id"],"status":item["status"],
                          "before":item["before"],"after":item["after"]},ensure_ascii=False),flush=True)
    except Exception as exc:
        item["status"]="ERROR"
        item["error"]=str(exc)[:550]
        print("SEO_PRODUCT "+json.dumps({"slug":slug,"status":"ERROR","error":item["error"]},ensure_ascii=False),flush=True)
    report["items"].append(item)
    persist()
def main():
    health=request("GET","/v1/Health")
    if val(health,"Ok") is not True:raise RuntimeError("API health failed")
    for t in TARGETS:apply(t)
    report["finishedUtc"]=datetime.now(timezone.utc).isoformat()
    report["summary"]={k:sum(x.get("status")==k for x in report["items"]) for k in ("APPLIED_VERIFIED","NO_CHANGE_ALREADY_MATCHES","ERROR")}
    report["status"]="SUCCESS" if report["summary"]["ERROR"]==0 else "PARTIAL_OR_FAILED"
    persist()
    print("SEO_DEPLOYMENT_SUMMARY "+json.dumps(report["summary"],ensure_ascii=False),flush=True)
    return 0 if report["summary"]["ERROR"]==0 else 2
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        report["status"]="FATAL_ERROR"
        report["error"]=str(e)[:550]
        persist()
        raise
