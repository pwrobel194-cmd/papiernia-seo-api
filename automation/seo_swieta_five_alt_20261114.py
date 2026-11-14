#!/usr/bin/env python3
"""Owner-approved image ALT and Title improvements, 14 Nov 2026.
Existing SEO API v3 preview/commit, one gallery picture for each of 5 products.
No image file, order, slug, title/meta SEO, or HTML edits.
"""
import json,os,sys
from pathlib import Path
from datetime import datetime, timezone
import requests
API="https://papiernia.net.pl/papiernia-seo-api"
KEY=os.getenv("PAPIERNIA_SEO_API_KEY","")
if not KEY:raise RuntimeError("Missing existing API secret")
s=requests.Session()
s.headers.update({"X-Papiernia-SEO-Key":KEY,"Accept":"application/json"})
targets=[
 (4917,"magnesy-swiateczne",5598,"Magnes świąteczny z logo firmy i życzeniami na złotym kartonie","Magnes świąteczny z logo firmy – Papiernia"),
 (4918,"swieczki-dla-pracownikow-upominek-swiateczny-dla-firm",5615,"Biała świeczka serce w opakowaniu EKO z logo dla pracowników na święta","Świeczka świąteczna serce dla pracowników – Papiernia"),
 (4946,"tani-upominek-dla-klientow-na-swieta",5993,"Ciasteczko z wróżbą z personalizowaną etykietą świąteczną dla klientek","Ciasteczko z wróżbą na Święta z logo – Papiernia"),
 (4921,"notesy-swiateczne-upominki-swiateczne",5664,"Mini notesiki świąteczne z ołówkiem i bilecikiem z logo firmy","Notesiki świąteczne z ołówkiem – Papiernia"),
 (4952,"lizaki-reklamowe-z-nadrukiem-logo-upominek-na-swieta",6070,"Lizak świąteczny z logo i etykietą dla klientek salonu","Lizak reklamowy z logo dla salonu na Święta – Papiernia")
]
OUT=Path("reports/christmas-five-alt-20261114")
OUT.mkdir(parents=True,exist_ok=True)
report={"createdUtc":datetime.now(timezone.utc).isoformat(),"scope":"One original product image ALT/Title per target","items":[],"status":"STARTED"}
def save():
 (OUT/"alt-deployment-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def v(o,k,default=None):
 return o.get(k,o.get(k[0].lower()+k[1:],default)) if isinstance(o,dict) else default
def api(method,endpoint,**opts):
 r=s.request(method,API+endpoint,timeout=45,**opts)
 if r.status_code>=400:raise RuntimeError("%s %s HTTP %s: %s"%(method,endpoint,r.status_code,r.text[:300]))
 return r.json()
def snapshot(pid):
 return api("GET","/v3/ProductSnapshot/"+str(pid))
def find_pic(snap,picture_id):
 return next((p for p in v(snap,"Pictures",[]) if int(v(p,"Id",-1))==picture_id),None)
def core(snap):
 return {k:v(snap,k) for k in ("Name","Sku","Slug","ShortDescription","FullDescription","MetaTitle","MetaDescription","MetaKeywords","Published","Deleted")}
def pic_ids(snap):
 return [int(v(p,"Id",-1)) for p in v(snap,"Pictures",[])]
def run():
 for pid,slug,picid,alt,title in targets:
  entry={"id":pid,"slug":slug,"pictureId":picid}
  try:
   before=snapshot(pid)
   if v(before,"Slug")!=slug or v(before,"Published") is not True or v(before,"Deleted"):
    raise RuntimeError("Product changed or unpublished")
   pic=find_pic(before,picid)
   if not pic:raise RuntimeError("Picture no longer assigned to product")
   entry["before"]={"alt":v(pic,"AltAttribute"),"title":v(pic,"TitleAttribute")}
   entry["after"]={"alt":alt,"title":title}
   (OUT/(slug+"-before-picture.json")).write_text(json.dumps({"productId":pid,"picture":pic},ensure_ascii=False,indent=2),encoding="utf-8")
   if entry["before"]==entry["after"]:
    entry["status"]="NO_CHANGE"
   else:
    payload={"scope":"product","pictureId":picid,
     "altAttribute":alt,"titleAttribute":title,
     "reason":"Zatwierdzone przez właściciela 14.11.2026 — doprecyzowanie ALT i Title zdjęcia głównego bez zmiany pliku."}
    preview=api("POST","/v3/PreviewPictureMetadata/"+str(pid),json=payload)
    token=v(preview,"ApprovalToken")
    if not token:raise RuntimeError("No approval token from image preview")
    reread=snapshot(pid)
    if core(before)!=core(reread) or pic_ids(before)!=pic_ids(reread) or find_pic(before,picid)!=find_pic(reread,picid):
     raise RuntimeError("Unexpected change between snapshot and commit")
    commit=api("PUT","/v3/CommitPictureMetadata/"+str(pid),json={**payload,"approvalToken":token})
    if v(commit,"Committed") is not True:raise RuntimeError("API did not confirm picture metadata commit")
    after=snapshot(pid)
    updated=find_pic(after,picid)
    if not updated or v(updated,"AltAttribute")!=alt or v(updated,"TitleAttribute")!=title:
     raise RuntimeError("Picture metadata readback mismatch")
    if core(after)!=core(before) or pic_ids(after)!=pic_ids(before):
     raise RuntimeError("Product content or gallery order changed")
    entry["status"]="APPLIED_VERIFIED"
  except Exception as e:
   entry["status"]="ERROR"
   entry["error"]=str(e)[:500]
  report["items"].append(entry)
  save()
  print("ALT_PRODUCT "+json.dumps(entry,ensure_ascii=False),flush=True)
  # First-time API v3 picture metadata write: stop on any failure, never continue blindly.
  if entry["status"]=="ERROR":
   break
 report["finishedUtc"]=datetime.now(timezone.utc).isoformat()
 report["summary"]={k:sum(x.get("status")==k for x in report["items"]) for k in ("APPLIED_VERIFIED","NO_CHANGE","ERROR")}
 report["status"]="SUCCESS" if len(report["items"])==len(targets) and report["summary"]["ERROR"]==0 else "STOPPED"
 save()
 print("ALT_DEPLOYMENT_SUMMARY "+json.dumps(report["summary"],ensure_ascii=False),flush=True)
 return 0 if report["status"]=="SUCCESS" else 2
if __name__=="__main__":sys.exit(run())
