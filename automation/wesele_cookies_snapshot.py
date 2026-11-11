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

from html import unescape
expected={
 "category":"Ciasteczka z wróżbą na wesele – podziękowania dla gości",
 "winietka":"Ciasteczko z wróżbą i winietką 2w1 na wesele",
 "torebka":"Ciasteczko z wróżbą w torebce na wesele",
 "biale":"Ciasteczko z wróżbą w białym pudełeczku na wesele",
 "eko":"Ciasteczko z wróżbą w pudełeczku EKO na wesele",
 "rozowe":"Ciasteczko z wróżbą w różowym pudełeczku na wesele",
 "bilecik":"Ciasteczko z wróżbą ze złotym bilecikiem na ślub"
}
public={}
for label,slug in URLS.items():
  try:
    response=requests.get(BASE+slug,params={"seo_check":"202611111653"},headers={"Cache-Control":"no-cache","Pragma":"no-cache","User-Agent":"Mozilla/5.0 (compatible; PapierniaSeoAudit/1.0)"},timeout=35)
    match=re.search(r'<h1[^>]*>(.*?)</h1\s*>',response.text,flags=re.I|re.S)
    h1=unescape(re.sub(r'<[^>]+>'," ",match.group(1)).strip()) if match else None
    h1=re.sub(r"\s+"," ",h1).strip() if h1 else None
    title_match=re.search(r'<title[^>]*>(.*?)</title\s*>',response.text,flags=re.I|re.S)
    title=unescape(re.sub(r'<[^>]+>'," ",title_match.group(1)).strip()) if title_match else None
    has_new_h2=bool(re.search(r'Ciasteczka z wróżbą na wesele – oryginalne podziękowania',response.text))
    public[label]={"http":response.status_code,"h1":h1,"expected":expected[label],"h1Matches":h1==expected[label],"title":title,"newCategoryCopySeen":has_new_h2 if label=="category" else None}
    print("PUBLIC",label,"http",response.status_code,"H1_OK",h1==expected[label],"H1",str(h1)[:140],"TITLE",str(title)[:140], "CATEGORY_COPY",has_new_h2 if label=="category" else "-",flush=True)
  except Exception as e:
    public[label]={"error":str(e)}
    print("PUBLIC_ERROR",label,str(e)[:180],flush=True)
record["public"]=public
out.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
