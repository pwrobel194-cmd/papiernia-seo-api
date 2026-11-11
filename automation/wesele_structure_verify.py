import os,json,re,requests,pathlib
from bs4 import BeautifulSoup
from datetime import datetime,timezone

BASE="https://papiernia.net.pl"
OUT=pathlib.Path("reports/wesele-structure")
data=json.loads((OUT/"snapshot.json").read_text(encoding="utf-8"))
records={"timestamp":datetime.now(timezone.utc).isoformat(),"categoryPages":[],"productPages":[]}
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; PapierniaSEO-Verification/1.0)","Cache-Control":"no-cache"})
fail=[]
for k,v in data["categories"].items():
 url=BASE+"/"+v["slug"]
 r=S.get(url,timeout=45)
 doc=BeautifulSoup(r.text,"html.parser")
 h1=doc.h1.get_text(" ",strip=True) if doc.h1 else None
 title=doc.title.get_text(" ",strip=True) if doc.title else None
 canonical=(doc.select_one('link[rel="canonical"]') or {}).get("href")
 marker='data-papiernia-wesele-seo="2026-11-11"'
 hasmarker=marker in r.text
 needles={"main":"Wybierz podziękowania dla gości weselnych według rodzaju upominku","candles":"Mini świeczki i podziękowania dla gości weselnych","chocolates":"Czekoladki ślubne dla gości – dostępne warianty","magnets":"Wybierz magnesy jako podziękowania na wesele","sweets":"Słodkie upominki weselne – wybierz rodzaj słodyczy","funny":"Śmieszne podziękowania – produkty i wzory z humorem","scratch":"Zdrapki weselne – prezent i zabawa na przyjęciu","placecards":"Winietki i podziękowanie dla gości w jednym","tea":"Herbatka dla gości na wesele – personalizowany upominek"}
 newtext=needles.get(k,"") in doc.get_text(" ",strip=True) if k!="cookies" else None
 api_text=v["snapshot"]["Description"] or ""
 api_marker=marker in api_text
 result={"key":k,"url":url,"http":r.status_code,"h1":h1,"title":title,"canonical":canonical,"newSeoSectionSeen":hasmarker,"newSectionTextVisible":newtext,"apiHasMarker":api_marker}
 print("DIAGNOSTIC",k,"api",api_marker,"public_text",newtext,"public_marker",hasmarker,flush=True)
 records["categoryPages"].append(result)
 if r.status_code!=200 or canonical!=url or (k!="cookies" and not hasmarker):fail.append("category "+k)
 print("PUBLIC_CATEGORY",k,r.status_code,"MARKER",hasmarker,"H1",h1,"CANONICAL",canonical,flush=True)
for slug,x in data["products"].items():
 if x["id"] in [4905,4895] or x["id"] in [4884,4898,4899,4888,4900,4904]:continue
 url=BASE+"/"+slug
 r=S.get(url,timeout=45)
 doc=BeautifulSoup(r.text,"html.parser")
 h1=doc.h1.get_text(" ",strip=True) if doc.h1 else None
 canonical=(doc.select_one('link[rel="canonical"]') or {}).get("href")
 hasmarker='data-papiernia-wesele-seo="2026-11-11"' in r.text
 result={"id":x["id"],"slug":slug,"http":r.status_code,"h1":h1,"canonical":canonical,"linkedSectionSeen":hasmarker}
 records["productPages"].append(result)
 if r.status_code!=200 or canonical!=url or not hasmarker:fail.append("product "+str(x["id"]))
 print("PUBLIC_PRODUCT",x["id"],r.status_code,"MARKER",hasmarker,"CANONICAL",canonical,flush=True)
records["warnings"]=fail
(OUT/"public-verification.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
print("PUBLIC_COMPLETE","categories",len(records["categoryPages"]),"products",len(records["productPages"]),"warnings",len(fail),flush=True)
