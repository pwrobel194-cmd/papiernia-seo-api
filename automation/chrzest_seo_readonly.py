"""Read-only SEO Chrzest audit using existing Papiernia SEO API v3.
Never modifies shop, no POST/PUT. Summary artifact contains no secrets.
"""
import os, requests, json, pathlib, re, hashlib
from bs4 import BeautifulSoup
ROOT="https://papiernia.net.pl"
BASE=ROOT+"/papiernia-seo-api"
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]})
out=pathlib.Path("audit/chrzest-20261108");out.mkdir(parents=True,exist_ok=True)
TARGETS=[
(ROOT+"/chrzest","Category"),
(ROOT+"/podziekowanie-za-przybycie-na-chrzest","Product"),
(ROOT+"/herbata-podziekowania-dla-gosci-chrzest","Product")]
def get_api(path,params=None):
 r=session.get(BASE+path,params=params,timeout=45);r.raise_for_status();return r.json()
def fld(d,k):return d.get(k,d.get(k[0].upper()+k[1:]))
def protect(x):return {"sha256":hashlib.sha256(x.encode("utf-8")).hexdigest(),"len":len(x)}
def api_one(url,typ):
 res=get_api("/v1/Resolve",{"url":url})
 id=fld(res,"id"); assert str(fld(res,"entity")).lower()==typ.lower() and id
 raw=get_api(f"/v3/{typ}Snapshot/{id}")
 cur=raw.get("data",raw.get("snapshot",raw))
 assert isinstance(cur,dict)
 html=fld(cur,"description") if typ=="Category" else fld(cur,"fullDescription")
 html=html or ""
 soup=BeautifulSoup(html,"html.parser")
 fields=("name","metaTitle","metaDescription","metaKeywords","seName","published","deleted")
 if typ=="Product":fields+=("shortDescription",)
 data={k:fld(cur,k) for k in fields}
 output={"type":typ,"url":url,"id":id,
  "fields":data,"descriptionHtml":html,
  "html":protect(html),
  "headings":[{"level":h.name,"text":h.get_text(" ",strip=True)} for h in soup.find_all(["h1","h2","h3","h4"])],
  "links":[{"href":x.get("href"),"text":x.get_text(" ",strip=True)} for x in soup.find_all("a")],
  "images":[{"src":im.get("src"),"alt":im.get("alt"),"title":im.get("title")} for im in soup.find_all("img")]}
 if typ=="Product":
  try: output["categories"]=get_api(f"/v3/ProductCategories/{id}")
  except requests.exceptions.HTTPError as ex:output["categoriesError"]=str(ex)
 return output
def public_one(url):
 r=requests.get(url,timeout=50,headers={"User-Agent":"Mozilla/5.0 (compatible; SEOInspection/1.0)"})
 soup=BeautifulSoup(r.text,"html.parser")
 title=soup.title.get_text(" ",strip=True) if soup.title else None
 metas=[m for m in soup.find_all("meta") if m.get("name","").lower() in ("description","robots","googlebot")]
 can=soup.find("link",rel="canonical")
 products=soup.select(".product-item")
 extracted=[{"title":p.select_one(".product-title").get_text(" ",strip=True) if p.select_one(".product-title") else None,
 "href":p.select_one(".product-title a").get("href") if p.select_one(".product-title a") else None,
 "img_alt":p.select_one("img").get("alt") if p.select_one("img") else None} for p in products]
 ld=[]
 for x in soup.find_all("script",type="application/ld+json"):
  try:
   d=json.loads(x.string or x.get_text())
   ld.append(d.get("@type") if isinstance(d,dict) else "array")
  except:ld.append("invalid")
 return {"url":url,"status":r.status_code,"canonical":can.get("href") if can else None,
  "htmlTitle":title,"headings":[{"level":h.name,"text":h.get_text(" ",strip=True)} for h in soup.find_all(["h1","h2","h3"])][:40],
  "metas":[{"name":m.get("name"),"content":m.get("content")} for m in metas],
  "products":extracted,"jsonldTypes":ld}
def main():
 data={"api":[],"public":[]}
 for url,typ in TARGETS:
  v=api_one(url,typ);data["api"].append(v)
  pub=public_one(url);data["public"].append(pub)
  print(json.dumps({"url":url,"id":v["id"],"type":typ,
    "metaTitle":v["fields"]["metaTitle"],"metaDescription":v["fields"]["metaDescription"],
    "name":v["fields"]["name"],"htmlLen":v["html"]["len"],
    "headings":v["headings"][:12],
    "imgCount":len(v["images"]),"linkCount":len(v["links"]),
    "publicStatus":pub["status"],"publicCanonical":pub["canonical"],
    "publicProductCount":len(pub["products"]),"publicProducts":pub["products"][:20],
    "jsonldTypes":pub["jsonldTypes"]},ensure_ascii=False))
 (out/"live-audit.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
