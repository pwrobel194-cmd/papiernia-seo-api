#!/usr/bin/env python3
# Papiernia Urodziny — controlled SEO update. Only FullDescription and safe first-image ALT.
# Keep Name/H1, SeName, ShortDescription, MetaTitle, MetaDescription, prices, image files, model sections unchanged.
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://papiernia.net.pl"
API=BASE+"/papiernia-seo-api/v1"
HUB=BASE+"/podziekowania-upominki-na-urodziny"
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY","")
if not KEY:
    raise RuntimeError("Missing PAPIERNIA_SEO_API_KEY")
S=requests.Session()
S.headers.update({"X-Papiernia-SEO-Key":KEY})
WORK="urodziny-seo-20261026"
BACKUP=Path("backups/urodziny-20261026")
REPORT=Path("reports/urodziny-seo-20261026-result.json")
BACKUP.mkdir(parents=True,exist_ok=True)
REPORT.parent.mkdir(parents=True,exist_ok=True)
PRODUCTS=[
 {"slug":"upominek-urodzinowy-dla-gosci-ciasteczko-z-wrozba","focus":"Ciasteczko z wróżbą na urodziny","text":"Ciasteczko z wróżbą i personalizowanym bilecikiem sprawdzi się jako zabawny drobiazg dla gości przyjęcia urodzinowego.","alt":"Ciasteczko z wróżbą na urodziny z personalizowanym bilecikiem"},
 {"slug":"oryginalne-podziekowania-dla-gosci-na-urodziny","focus":"Herbatka z personalizowaną etykietą na urodziny","text":"Herbatka w papierowym opakowaniu EKO z dedykacją to niewielki prezent dla uczestników rodzinnego jubileuszu.","alt":"Herbatka w opakowaniu EKO z etykietą na urodziny"},
 {"slug":"personalizowane-cukierki-na-urodziny","focus":"Personalizowane cukierki na urodziny","text":"Trzy kolorowe karmelki z bilecikiem i własnym tekstem to słodki drobiazg dla gości urodzinowych.","alt":"Trzy kolorowe cukierki na urodziny z personalizowanym bilecikiem"},
 {"slug":"czekoladki-dla-gosci-na-urodziny","focus":"Białe czekoladki na urodziny z etykietą","text":"Mała biała czekoladka z personalizowaną etykietą jest słodkim podziękowaniem; etykietę należy przykleić samodzielnie.","alt":"Biała czekoladka na urodziny z personalizowaną etykietą"},
 {"slug":"czekoladki-dla-gosci-na-urodziny-ciemna-czekolada","focus":"Ciemne czekoladki na urodziny z etykietą","text":"Mała ciemna czekoladka z krótkim tekstem na personalizowanej naklejce to słodka pamiątka dla gości.","alt":"Ciemna czekoladka na urodziny z personalizowaną etykietą"},
 {"slug":"upominki-z-czekolada-dla-gosci-na-urodziny","focus":"Czekoladka w białym opakowaniu na urodziny","text":"Ciemna czekoladka w białym opakowaniu z personalizowaną etykietą wyróżnia się elegancką oprawą na przyjęcie urodzinowe.","alt":"Czekoladka w białym opakowaniu z etykietą na urodziny"},
 {"slug":"podziekowania-za-przybycie-na-urodziny","focus":"Kartka A6 z mleczną czekoladką na urodziny","text":"Kartka z personalizowaną dedykacją i mleczną czekoladką ma format A6; dołączony celofan służy do samodzielnego zapakowania.","alt":"Kartka A6 z mleczną czekoladką i podziękowaniem na urodziny"},
 {"slug":"magnesy-na-urodziny","focus":"Złote magnesy na urodziny z dedykacją","text":"Błyszcząca złota pamiątka z funkcją magnesu i własnym tekstem jest drobnym podziękowaniem za udział w przyjęciu.","alt":"Złoty personalizowany magnes jako podziękowanie na urodziny"}
]
IMG=re.compile(r"<img\b[^>]*>",re.I)
META_KEYS=["Name","SeName","ShortDescription","MetaTitle","MetaDescription","MetaKeywords","Published","Deleted"]
def get(ep,params=None):
    r=S.get(API+"/"+ep,params=params,timeout=35)
    r.raise_for_status()
    return r.json()
def put(ep,data,dry):
    r=S.put(API+"/"+ep,params={"dryRun":str(dry).lower()},json=data,timeout=50)
    r.raise_for_status()
    return r.json()
def write_report():
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def new_html(before,item):
    old=before or ""
    if not old.strip():
        raise RuntimeError("Empty existing FullDescription; do not replace")
    output=old
    leadmark="pn-urodziny-opis-20261026"
    if leadmark not in output:
        lead='<p class="'+leadmark+'" style="line-height:1.65;text-align:left;"><strong>'+html.escape(item["focus"])+'.</strong> '+html.escape(item["text"])+'</p>'
        hmatch=re.search(r"</h[2-6]\s*>",output,re.I)
        if hmatch and hmatch.start()<1400:
            output=output[:hmatch.end()]+"\n"+lead+output[hmatch.end():]
        else:
            output=lead+"\n"+output
    # Correct only unambiguous text in full descriptions without changing image/link markup.
    corrections={
        "uoprzonwej":"urodzinowej",
        "Nie wiesz jak wyrazić podziękować":"Nie wiesz, jak podziękować",
        "ciasteczkiem z wróżba":"ciasteczkiem z wróżbą",
        "upominek urodzinowy z dużą elastycznością":"upominek urodzinowy z możliwością",
    }
    for a,b in corrections.items():
        if a in output:
            output=output.replace(a,b)
    if HUB not in output:
        output+='\n<p class="pn-urodziny-hub-20261026" style="line-height:1.65;margin:16px 0;">Zobacz też <a href="'+HUB+'" title="Podziękowania dla gości na urodziny">podziękowania dla gości na urodziny</a> – porównaj różne rodzaje drobnych upominków.</p>'
    if IMG.findall(old)!=IMG.findall(output):
        raise RuntimeError("Existing image tags changed")
    if len(output)>100000:
        raise RuntimeError("FullDescription too long")
    return output
def maybe_update_alt(pid, item, entry):
    pics=get("ProductPictures/"+str(pid))
    arr=pics.get("pictures",[])
    entry["pictureCount"]=len(arr)
    if not arr:
        entry["altStatus"]="NO_PICTURES"
        return
    first=arr[0]
    current=(first.get("AltAttribute") or "").strip()
    entry["firstImageAltBefore"]=current
    # Existing descriptive ALT is retained. Never modify model-graphic picture ALT.
    # Do not alter an ALT when its picture name appears to be a gallery of design models.
    picname=(first.get("SeoFilename") or "").lower()
    if any(word in picname for word in ["modele","model-graficz","wzory","grafik-"]):
        entry["altStatus"]="MODEL_IMAGE_PRESERVED"
        return
    if current and len(current)>=18:
        entry["altStatus"]="DESCRIPTIVE_ALT_PRESERVED"
        return
    alt=item["alt"]
    payload={"PictureId":first["Id"],"AltAttribute":alt,"RequestId":WORK+"-alt-"+str(first["Id"]),"Reason":"Unique descriptive ALT for birthday product main image; preserve image file."}
    d=put("UpdatePictureAlt/"+str(pid),payload,True)
    if not d.get("ok") or d.get("dryRun") is not True:
        raise RuntimeError("ALT dryRun failed")
    w=put("UpdatePictureAlt/"+str(pid),payload,False)
    if not w.get("ok") or w.get("dryRun") is not False:
        raise RuntimeError("ALT PUT failed")
    pics_after=get("ProductPictures/"+str(pid))
    restored=next((p for p in pics_after.get("pictures",[]) if p.get("Id")==first["Id"]),None)
    if not restored or (restored.get("AltAttribute") or "").strip()!=alt:
        raise RuntimeError("ALT read-back mismatch")
    entry["altStatus"]="ALT_APPLIED_VERIFIED"
    entry["firstImageAltAfter"]=alt

report={"createdUtc":datetime.now(timezone.utc).isoformat(),"category":HUB,
        "scope":["FullDescription text lead","product-to-category internal link","safe correction of typos","first image ALT only when missing"],
        "unchanged":["Name/H1","SeName/URL","ShortDescription","MetaTitle","MetaDescription","MetaKeywords","all image tags","prices","gallery files"],"results":[]}
def main():
    health=get("Health")
    if health.get("ok") is not True:
        raise RuntimeError("API health check failed")
    seen=set()
    for item in PRODUCTS:
        slug=item["slug"]
        entry={"slug":slug,"url":BASE+"/"+slug}
        try:
            ident=get("Resolve",{"url":entry["url"]})
            if ident.get("entity")!="Product" or ident.get("slug")!=slug or not ident.get("Published") or ident.get("Deleted"):
                raise RuntimeError("Resolve mismatch or inactive product")
            pid=int(ident["id"])
            if pid in seen: raise RuntimeError("Duplicate product ID")
            seen.add(pid)
            entry["id"]=pid
            before=get("Product/"+str(pid))
            if before.get("SeName")!=slug or not before.get("Published") or before.get("Deleted"):
                raise RuntimeError("Product identity changed or inactive")
            (BACKUP/(slug+".json")).write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding="utf-8")
            original=before.get("FullDescription") or ""
            updated=new_html(original,item)
            if updated!=original:
                payload={"FullDescription":updated,"RequestId":WORK+"-full-"+str(pid),"Reason":"Birthday SEO: product-specific description lead, natural hub link and small text fixes; no H1, meta, pictures or short description changes."}
                dry=put("UpdateProduct/"+str(pid),payload,True)
                if dry.get("ok") is not True or dry.get("dryRun") is not True:raise RuntimeError("FullDescription dry-run failed")
                applied=put("UpdateProduct/"+str(pid),payload,False)
                if applied.get("ok") is not True or applied.get("dryRun") is not False:raise RuntimeError("FullDescription PUT failed")
            after=get("Product/"+str(pid))
            if any(before.get(k)!=after.get(k) for k in META_KEYS):
                raise RuntimeError("Immutable fields changed unexpectedly")
            if (after.get("FullDescription") or "")!=updated:
                raise RuntimeError("FullDescription read-back mismatch")
            if IMG.findall(original)!=IMG.findall(updated):
                raise RuntimeError("Image tags mismatch")
            entry["fullDescriptionStatus"]="APPLIED_VERIFIED" if updated!=original else "NO_CHANGE"
            # Allow alt check to fail independently; don't misreport the verified description.
            try:
                maybe_update_alt(pid,item,entry)
            except Exception as exc:
                entry["altStatus"]="ALT_ERROR"
                entry["altError"]=str(exc)
            entry["status"]="APPLIED_VERIFIED"
        except Exception as exc:
            entry["status"]="ERROR"
            entry["error"]=str(exc)
        report["results"].append(entry)
        write_report()
        print(json.dumps({k:entry.get(k) for k in ("slug","id","status","fullDescriptionStatus","altStatus","error","altError")},ensure_ascii=False),flush=True)
    report["finishedUtc"]=datetime.now(timezone.utc).isoformat()
    report["summary"]={
        "productsVerified":sum(x["status"]=="APPLIED_VERIFIED" for x in report["results"]),
        "productsError":sum(x["status"]=="ERROR" for x in report["results"]),
        "altApplied":sum(x.get("altStatus")=="ALT_APPLIED_VERIFIED" for x in report["results"]),
        "altPreserved":sum(x.get("altStatus") in ("DESCRIPTIVE_ALT_PRESERVED","MODEL_IMAGE_PRESERVED") for x in report["results"]),
        "altError":sum(x.get("altStatus")=="ALT_ERROR" for x in report["results"])
    }
    write_report()
    print("BIRTHDAY_SEO_SUMMARY="+json.dumps(report["summary"],ensure_ascii=False),flush=True)
    return 2 if report["summary"]["productsError"] or report["summary"]["altError"] else 0
if __name__=="__main__":
    sys.exit(main())
