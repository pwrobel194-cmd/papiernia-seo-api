import os, json, requests, pathlib, re, time, hashlib
from datetime import datetime, timezone
BASE="https://papiernia.net.pl"
ROOT=BASE+"/papiernia-seo-api"
H={"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]}
URLS={
"category":"/ciasteczka-z-wrozba-dla-gosci-na-wesele",
"winietka":"/podziekowania-dla-gosci-z-winietka",
"torebka":"/podziekowanie-na-slub-torebka-z-ciasteczkiem-z-wrozba",
"biale":"/ciasteczka-z-wrozba-na-podziekowania",
"eko":"/podziekowania-dla-gosci-ciasteczko-z-wrozba",
"rozowe":"/ciasteczka-z-wrozba-wesele",
"bilecik":"/ciasteczka-z-wrozba-slub"
}
s=requests.Session();s.headers.update(H)
def get(route,params=None):
    r=s.get(ROOT+route,params=params,timeout=35);r.raise_for_status();return r.json()
record={"date":datetime.now(timezone.utc).isoformat(),"source":"live authenticated v3 snapshots","items":{}}
for label, slug in URLS.items():
    entry={"url":BASE+slug}
    try:
        resolved=get("/v1/Resolve",{"url":entry["url"]})
        entry["resolve"]=resolved
        eid=resolved.get("id") or resolved.get("Id")
        if not eid: raise RuntimeError("No id in resolve")
        entity="Category" if label=="category" else "Product"
        entry["snapshot"]=get("/v3/"+entity+"Snapshot/"+str(eid))
        if label!="category":
            for kind in ("ProductCategories","ProductHtmlImages","ProductPictures"):
                try: entry[kind]=get("/v3/"+kind+"/"+str(eid))
                except Exception as e: entry[kind+"Error"]=str(e)[:200]
        else:
            try: entry["CategoryPicture"]=get("/v3/CategoryPicture/"+str(eid))
            except Exception as e: entry["CategoryPictureError"]=str(e)[:200]
        ss=entry["snapshot"]
        if isinstance(ss,dict):
            print("ITEM",label,"id",eid,"keys",list(ss.keys()),"name",str(ss.get("name",ss.get("Name","")))[:140])
            for k,v in ss.items():
                if any(t in k.lower() for t in ["description","picture","categor","name","meta","sename","published"]):
                    txt=json.dumps(v,ensure_ascii=False)
                    print("FIELD",label,k,"length",len(txt),"preview",txt[:320])
        print("RESOLVED",label,json.dumps(resolved,ensure_ascii=False)[:500])
    except Exception as e:
        entry["error"]=str(e)
        print("ERROR",label,str(e)[:400])
    record["items"][label]=entry
out=pathlib.Path("reports/wesele-cookies-snapshot.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUMMARY",json.dumps({k:{"id":v.get("resolve",{}).get("id"),"error":v.get("error")} for k,v in record["items"].items()},ensure_ascii=False))
