#!/usr/bin/env python3
"""Read-only SEO audit of 38 Christmas products, category and related sources.

Reads existing SEO API GET endpoints and publicly visible HTML only.
No PUT/POST, no changes to site content or indexing.
"""
import json, os, re, sys, time
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

SITE="https://papiernia.net.pl"
API=SITE+"/papiernia-seo-api/v3"
KEY=os.getenv("PAPIERNIA_SEO_API_KEY")
PLAN=Path("automation/christmas-h1-intents-20261106.json")
OUTPUT=Path("reports/christmas-links-schema-audit-20261108.json")
if not KEY: raise SystemExit("No API secret")
slugs=[x["slug"] for x in json.loads(PLAN.read_text(encoding="utf-8"))["products"]]
assert len(slugs)==38 and len(set(slugs))==38
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":KEY,"User-Agent":"PapierniaSEOReadOnlyAudit/1.0"})
public=requests.Session()
public.headers.update({"User-Agent":"Mozilla/5.0 (compatible; PapierniaSEOAudit/1.0)"})
report={"purpose":"READ ONLY 2026-11-08: product->category links, schema/Offer, technical indexing signals",
        "category":{},"products":[],"external_context_pages":[],"errors":[],"robots":{},
        "counts":{}}
def save():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

def get_api(url,params=None):
    r=session.get(url,params=params,timeout=35)
    r.raise_for_status()
    return r.json()

def field(o,name,default=None):
    return o.get(name,o.get(name[:1].lower()+name[1:],default))

def text_content(s):
    return BeautifulSoup(s or "","html.parser").get_text(" ",strip=True)

def doc_links(s):
    soup=BeautifulSoup(s or "", "html.parser")
    links=[]
    for a in soup.select("a[href]"):
        href=a.get("href","").strip()
        if not href or href.startswith(("#","mailto:","tel:","javascript:")):continue
        abs_href=urljoin(SITE,href)
        if urlparse(abs_href).netloc not in ("papiernia.net.pl","www.papiernia.net.pl"):continue
        links.append({"href":abs_href,"anchor":a.get_text(" ",strip=True),"title":a.get("title",""),
                      "has_image":bool(a.find("img")),"rel":a.get("rel",[])})
    return links

def extract_jsonld(soup):
    results=[]; errors=0
    def gather(value):
        if isinstance(value,list):
            for e in value:gather(e)
        elif isinstance(value,dict):
            results.append(value)
            if "@graph" in value:gather(value["@graph"])
            for k in ("mainEntity",):
                if k in value and isinstance(value[k],(dict,list)):gather(value[k])
    for script in soup.find_all("script",attrs={"type":re.compile("ld\\+json",re.I)}):
        try:gather(json.loads(script.string or script.get_text()))
        except Exception:errors+=1
    def types(v):
        return [str(x).lower() for x in (v if isinstance(v,list) else [v])]
    products=[];offers=[]; type_count={}
    for item in results:
        t=item.get("@type",[])
        for k in types(t):type_count[k]=type_count.get(k,0)+1
        if "product" in types(t):
            products.append({k:item.get(k) for k in ("name","sku","offers","aggregateRating","review","image") if k in item})
            off=item.get("offers")
            if off is not None:offers.extend(off if isinstance(off,list) else [off])
        if "offer" in types(t):offers.append(item)
    clean_offers=[]
    for x in offers:
        if isinstance(x,dict):
            clean_offers.append({k:x.get(k) for k in ("price","priceCurrency","availability","url","priceSpecification","eligibleQuantity") if k in x})
    return {"types":type_count,"products":products[:2],"offers":clean_offers[:3],"parseErrors":errors}

def microdata(soup):
    types=[]
    for tag in soup.select("[itemscope][itemtype]"):
        typ=tag.get("itemtype","")
        types.append(typ)
    attrs=[]
    for x in soup.select("[itemprop=price],[itemprop=priceCurrency],[itemprop=availability]"):
        attrs.append({"itemprop":x.get("itemprop"),"content":x.get("content") or x.get("href") or x.get_text(" ",strip=True)[:80]})
    return {"types":list(dict.fromkeys(types))[:12],"fields":attrs[:16]}

def public_snapshot(url):
    r=public.get(url,timeout=40,allow_redirects=True)
    soup=BeautifulSoup(r.text,"html.parser")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    canon=soup.select_one('link[rel="canonical"]')
    robot=soup.select_one('meta[name="robots"]')
    h1=[x.get_text(" ",strip=True) for x in soup.find_all("h1")]
    price=soup.select_one(".product-price .price-value") or soup.select_one(".product-price span") or soup.select_one('[itemprop="price"]')
    visible_price=price.get_text(" ",strip=True)[:90] if price else None
    return {"requested":url,"final_url":r.url,"httpStatus":r.status_code,
            "title":title,"canonical":canon.get("href") if canon else None,
            "robots":robot.get("content") if robot else None,
            "h1":h1[:5],"html_bytes":len(r.content),
            "product_price_text":visible_price,
            "jsonld":extract_jsonld(soup),"microdata":microdata(soup),
            "contextual_links_in_main":doc_links(str(soup.select_one(".full-description") or soup.select_one(".page-body") or "")),
            "all_links_count":len(soup.select("a[href]")),
            "openGraphUrl": (soup.select_one('meta[property="og:url"]').get("content")
                             if soup.select_one('meta[property="og:url"]') else None)}

def main():
    report["health"]=get_api(SITE+"/papiernia-seo-api/v1/Health")
    resolver=get_api(SITE+"/papiernia-seo-api/v1/Resolve",params={"url":SITE+"/upominki-swiateczne"})
    report["category"]["resolve"]={k:resolver.get(k) for k in ("id","entity","slug")}
    cid=resolver.get("id",resolver.get("Id"))
    if not cid: raise RuntimeError("Cannot resolve category")
    report["category"]["api"]=get_api(API+f"/CategorySnapshot/{cid}")
    report["category"]["public"]=public_snapshot(SITE+"/upominki-swiateczne")
    for slug in slugs:
        product={"slug":slug,"url":SITE+"/"+slug}
        try:
            res=get_api(SITE+"/papiernia-seo-api/v1/Resolve",params={"url":product["url"]})
            pid=res.get("id",res.get("Id"))
            if not pid:raise RuntimeError("No ID")
            data=get_api(API+f"/ProductSnapshot/{pid}")
            if data.get("slug")!=slug:raise RuntimeError("Slug differs")
            product["id"]=pid
            product["name"]=field(data,"Name")
            product["published"]=data.get("Published",data.get("published"))
            product["full_description_len"]=len(field(data,"FullDescription") or "")
            product["short_description_len"]=len(field(data,"ShortDescription") or "")
            links=doc_links((data.get("FullDescription") or "")+" "+(data.get("ShortDescription") or ""))
            product["description_links"]=links
            product["category_description_links"]=[x for x in links if urlparse(x["href"]).path.rstrip("/")=="/upominki-swiateczne"]
            product["description_images"]=len(re.findall(r"<img\b",data.get("FullDescription") or "",re.I))
            publicpage=public_snapshot(product["url"])
            # cap to avoid bulky results from long descriptions and full nav
            pub_mainlinks=publicpage.pop("contextual_links_in_main",[])
            publicpage["category_links_in_page_body"]=[x for x in pub_mainlinks if urlparse(x["href"]).path.rstrip("/")=="/upominki-swiateczne"]
            product["public"]=publicpage
            print(json.dumps({"slug":slug,"id":pid,"http":publicpage["httpStatus"],
                     "descriptionToHub":len(product["category_description_links"]),
                     "ldProduct":len(publicpage["jsonld"]["products"]),
                     "ldOffer":len(publicpage["jsonld"]["offers"])},ensure_ascii=False),flush=True)
        except Exception as e:
            product["error"]=str(e)
            report["errors"].append({"slug":slug,"error":str(e)})
        report["products"].append(product)
        save()
    # Explore curated locations that could link contextually, excluding navigation.
    for suffix in ("/", "/podziekowania-dla-firm", "/slodkie-upominki-dla-klientow",
                   "/upominki-i-podziekowania-dla-gosci-weselnych", "/podziekowania-upominki-na-urodziny"):
        u=SITE+suffix
        try:
            pub=public_snapshot(u)
            anchors=pub.pop("contextual_links_in_main",[])
            report["external_context_pages"].append({"url":u,"status":pub["httpStatus"],
                "final_url":pub["final_url"],"title":pub["title"],
                "context_links_to_christmas":[x for x in anchors if urlparse(x["href"]).path.rstrip("/")=="/upominki-swiateczne"],
                "all_context_internal_links":len(anchors)})
        except Exception as e:
            report["external_context_pages"].append({"url":u,"error":str(e)})
    for suffix in ("/robots.txt","/sitemap.xml"):
        try:
            r=public.get(SITE+suffix,timeout=20)
            report["robots"][suffix]={"status":r.status_code,"final_url":r.url,
                    "content_type":r.headers.get("content-type"),"excerpt":r.text[:1800] if suffix=="/robots.txt" else r.text[:350]}
        except Exception as e: report["robots"][suffix]={"error":str(e)}
    ps=[p for p in report["products"] if not p.get("error")]
    report["counts"]={
        "planned":len(slugs),"inspected":len(ps),"errors":len(report["errors"]),
        "with_link_to_christmas_in_description":sum(bool(p.get("category_description_links")) for p in ps),
        "no_link_to_christmas_in_description":[p["slug"] for p in ps if not p.get("category_description_links")],
        "product_jsonld":sum(bool(p["public"]["jsonld"]["products"]) for p in ps),
        "offer_jsonld":sum(bool(p["public"]["jsonld"]["offers"]) for p in ps),
        "product_microdata":sum(any("product" in x.lower() for x in p["public"]["microdata"]["types"]) for p in ps),
        "with_any_canonical":sum(bool(p["public"]["canonical"]) for p in ps),
        "with_canonical_matching_url":sum((p["public"]["canonical"] or "").rstrip("/")==p["url"] for p in ps),
        "http200":sum(p["public"]["httpStatus"]==200 for p in ps),
        "noindex_meta":[p["slug"] for p in ps if "noindex" in (p["public"]["robots"] or "").lower()],
        "products_without_visible_price": [p["slug"] for p in ps if not p["public"]["product_price_text"]],
    }
    save()
    print("FINAL_COUNTS "+json.dumps(report["counts"],ensure_ascii=False),flush=True)

if __name__=="__main__":main()
