"""Read-only: live SEO API v3 snapshots for four Communion products.
Only GET requests; no store mutations, secrets never written to files.
"""
import os, json, pathlib, hashlib, requests, re
ROOT="https://papiernia.net.pl/papiernia-seo-api"
URLS=[
"https://papiernia.net.pl/czekoladki-komunijne-slodkie-podziekowanie",
"https://papiernia.net.pl/czekoladki-na-komunie-upominki-dla-gosci",
"https://papiernia.net.pl/magnesy-komunijne-dla-gosci",
"https://papiernia.net.pl/ciasteczka-z-wrozba-dla-gosci-na-komunie"
]
secret=os.environ["PAPIERNIA_SEO_API_KEY"]
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":secret,"Accept":"application/json"})
out=pathlib.Path("audit/komunia-20261108-stage2")
out.mkdir(parents=True,exist_ok=True)
def get(path, params=None):
 response=session.get(ROOT+path,params=params,timeout=40)
 response.raise_for_status()
 return response.json()
def field(obj,key):
 return obj.get(key,obj.get(key[0].upper()+key[1:]))
records=[]
for url in URLS:
 resolved=get("/v1/Resolve",{"url":url})
 entity=field(resolved,"entity"); product_id=field(resolved,"id")
 if str(entity).lower()!="product" or not str(product_id).isdecimal():
  raise RuntimeError("Cannot resolve product: "+url)
 raw=get(f"/v3/ProductSnapshot/{product_id}")
 current=raw.get("data",raw.get("snapshot",raw))
 if not isinstance(current,dict): raise RuntimeError("Unexpected snapshot response")
 selected={k:field(current,k) for k in (
 "name","metaTitle","metaDescription","metaKeywords","seName",
 "shortDescription","fullDescription","published","deleted","sku")}
 html=selected["fullDescription"] or ""
 imgs=re.findall(r"<img\b[^>]*>",html,re.I)
 links=re.findall(r"<a\b[^>]*>",html,re.I)
 record={"url":url,"id":int(product_id),"fields":selected,
  "fullDescription_sha256":hashlib.sha256(html.encode()).hexdigest(),
  "imageTags":imgs,"linkTags":links}
 records.append(record)
 print(json.dumps({"id":int(product_id),"url":url,"name":selected["name"],
  "metaTitle":selected["metaTitle"],"metaDescription":selected["metaDescription"],
  "shortDescription":(selected["shortDescription"] or "")[:450],
  "fullLength":len(html),"imgCount":len(imgs),"linkCount":len(links),
  "descriptionSha256":record["fullDescription_sha256"]},ensure_ascii=False))
(out/"snapshot.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
