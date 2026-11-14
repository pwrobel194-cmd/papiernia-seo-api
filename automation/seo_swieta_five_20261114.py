#!/usr/bin/env python3
"""Owner-approved Christmas SEO 2026: read-only live product inspection.
Uses existing Papiernia SEO API v3 and the preconfigured GitHub Actions secret.
No edits in this inspection stage.
"""
import hashlib
import html
import json
import os
import re
from pathlib import Path
import requests

BASE="https://papiernia.net.pl"
API=BASE+"/papiernia-seo-api"
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY","")
if not KEY: raise RuntimeError("Missing existing GitHub Actions API secret")
s=requests.Session()
s.headers.update({"X-Papiernia-SEO-Key":KEY,"Accept":"application/json"})
SLUGS=[
"magnesy-swiateczne",
"swieczki-dla-pracownikow-upominek-swiateczny-dla-firm",
"tani-upominek-dla-klientow-na-swieta",
"notesy-swiateczne-upominki-swiateczne",
"lizaki-reklamowe-z-nadrukiem-logo-upominek-na-swieta",
"lizaki-swiateczne",
]
def api(method, route, **kwargs):
    r=s.request(method,API+route,timeout=45,**kwargs)
    if r.status_code>=400:raise RuntimeError("HTTP %s for %s: %s"%(r.status_code,route,r.text[:250]))
    return r.json()
def v(x,k,default=None):
    return x.get(k,x.get(k[0].lower()+k[1:],default)) if isinstance(x,dict) else default
def contexts(string, pattern):
    out=[]
    for m in list(re.finditer(pattern,string or "",re.I))[:12]:
        out.append((string[max(0,m.start()-85):m.end()+100]).replace("\n"," ")[:210])
    return out
def main():
    health=api("GET","/v1/Health")
    if v(health,"Ok") is not True:raise RuntimeError("API health failed")
    d=Path("reports/christmas-five-20261114")
    d.mkdir(parents=True,exist_ok=True)
    report={"phase":"READ_ONLY","items":[]}
    for slug in SLUGS:
        item={"slug":slug}
        try:
            resolved=api("GET","/v1/Resolve",params={"url":BASE+"/"+slug})
            product_id=int(v(resolved,"Id"))
            if str(v(resolved,"Entity","")).lower()!="product":raise RuntimeError("not a product")
            snap=api("GET","/v3/ProductSnapshot/"+str(product_id))
            name=v(snap,"Name","")
            short=v(snap,"ShortDescription","") or ""
            full=v(snap,"FullDescription","") or ""
            photos=v(snap,"Pictures",[]) or []
            item.update({"id":product_id,"actualSlug":v(snap,"Slug"),"name":name,
                "published":v(snap,"Published"),"deleted":v(snap,"Deleted"),
                "updatedOnUtc":v(snap,"UpdatedOnUtc"),
                "metaTitle":v(snap,"MetaTitle"),"metaDescription":v(snap,"MetaDescription"),
                "shortLen":len(short),"fullLen":len(full),
                "shortSha":hashlib.sha256(short.encode()).hexdigest()[:12],
                "fullSha":hashlib.sha256(full.encode()).hexdigest()[:12],
                "htmlImages":len(re.findall(r'<img\\b[^>]*>',full,re.I)),
                "pictures":len(photos),
                "fullStart":re.sub(r'<[^>]+>',' ',html.unescape(full[:1200]))[:750],
                "shortStart":re.sub(r'<[^>]+>',' ',html.unescape(short[:550]))[:300],
                "year2025":contexts(full,r'2025'),
                "cookie":contexts(full,r'ciasteczk(?:iem|o|a|u|i)'),
                "dimensionTypo":contexts(full,r'7\\s*cm\\s*[x×]\\s*7\\s*m(?!m)'),
                "linksHub":full.count("/upominki-swiateczne"),
                "categories":v(snap,"Categories",[]),
                })
            # Save snapshots only as a temporary encrypted-by-GitHub Actions artifact,
            # never commit the content or user data to public repository.
            (d/(slug+".json")).write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")
        except Exception as e:
            item["error"]=str(e)[:450]
        report["items"].append(item)
        print("PRODUCT_SNAPSHOT "+json.dumps(item,ensure_ascii=False,default=str),flush=True)
    (d/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    if sum("error" in x for x in report["items"]):raise RuntimeError("One or more product snapshots unavailable")

if __name__=="__main__":main()
