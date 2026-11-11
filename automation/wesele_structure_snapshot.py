import os, json, requests, pathlib, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlsplit
from datetime import datetime,timezone

BASE="https://papiernia.net.pl"
ROOT=BASE+"/papiernia-seo-api"
S=requests.Session();S.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]})
OUT=pathlib.Path("reports/wesele-structure")
OUT.mkdir(parents=True,exist_ok=True)
SLUGS={
"main":"upominki-i-podziekowania-dla-gosci-weselnych",
"cookies":"ciasteczka-z-wrozba-dla-gosci-na-wesele",
"candles":"swieczki-podziekowania-dla-gosci-wesele",
"chocolates":"czekoladki-podziekowania-dla-gosci-wesele",
"magnets":"magnesy-dla-gosci-weselnych",
"sweets":"slodkie-podziekowania-dla-gosci-na-wesele",
"funny":"smieszne-podziekowania-dla-gosci-na-wesele",
"scratch":"zdrapki-weselne",
"placecards":"winietki-z-podziekowaniem",
"tea":"podziekowania-dla-gosci-weselnych-herbata"
}
def api(url,params=None):
    r=S.get(ROOT+url,params=params,timeout=45);r.raise_for_status();return r.json()
def public(url):
    r=requests.get(BASE+"/"+url,timeout=50,headers={"User-Agent":"Mozilla/5.0","Cache-Control":"no-cache"});r.raise_for_status();return r.text
records={"timestamp":datetime.now(timezone.utc).isoformat(),"categories":{},"products":{},"errors":[]}
for key,slug in SLUGS.items():
    try:
        resolve=api("/v1/Resolve",{"url":BASE+"/"+slug})
        eid=resolve.get("id")
        snap=api("/v3/CategorySnapshot/"+str(eid))
        html=public(slug)
        soup=BeautifulSoup(html,"html.parser")
        links=[]
        for a in soup.select(".product-item .product-title a, .product-item h2 a, .product-item h3 a"):
            href=a.get("href","")
            path=urlsplit(urljoin(BASE,href)).path.strip("/")
            if path and path not in links: links.append(path)
        all_pcount=len(links)
        records["categories"][key]={"id":eid,"slug":slug,"snapshot":snap,"product_links":links,"product_count_visible":all_pcount,"public_html_length":len(html),"h1":soup.h1.get_text(" ",strip=True) if soup.h1 else None,"canonical":(soup.select_one('link[rel="canonical"]') or {}).get("href")}
        print("CAT",key,"id",eid,"products",all_pcount,"name",snap.get("name"),"desc_chars",len(snap.get("Description") or ""),"pictures",(snap.get("picture") or {}).get("Id"),flush=True)
    except Exception as exc:
        records["errors"].append({"category":key,"error":str(exc)})
        print("ERROR",key,str(exc)[:190],flush=True)
    (OUT/"snapshot.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
links={}
for k,x in records["categories"].items():
    for link in x.get("product_links",[]):
        links.setdefault(link,[]).append(k)
print("UNIQUE_PRODUCT_SLUGS",len(links),flush=True)
for i,(slug,from_categories) in enumerate(links.items()):
    try:
        rr=api("/v1/Resolve",{"url":BASE+"/"+slug})
        if rr.get("entity")!="Product":continue
        eid=rr["id"]
        snap=api("/v3/ProductSnapshot/"+str(eid))
        records["products"][slug]={"id":eid,"from_categories":from_categories,"snapshot":snap}
        if i % 10 == 0:print("PRODUCT_PROGRESS",i,len(links),flush=True)
    except Exception as e:
        records["errors"].append({"product":slug,"error":str(e)})
    (OUT/"snapshot.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
print("SUMMARY",json.dumps({"cats":len(records["categories"]),"products":len(records["products"]),"errors":records["errors"][:12]},ensure_ascii=False),flush=True)
