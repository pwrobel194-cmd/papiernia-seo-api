"""Read-only birthday SEO API snapshot. Never writes to the shop."""
import json, os, pathlib, requests
BASE = "https://papiernia.net.pl/papiernia-seo-api/v1"
URLS = [
 "https://papiernia.net.pl/podziekowania-upominki-na-urodziny",
 "https://papiernia.net.pl/podziekowania-za-przybycie-na-urodziny",
 "https://papiernia.net.pl/oryginalne-podziekowania-dla-gosci-na-urodziny",
]
key=os.environ["PAPIERNIA_SEO_API_KEY"]
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":key})
out=pathlib.Path("birthday-seo-snapshot")
out.mkdir(exist_ok=True)
def get(path,params=None):
 r=session.get(f"{BASE}/{path}",params=params,timeout=35)
 r.raise_for_status()
 return r.json()
health=get("Health")
if not health.get("ok"):
 raise RuntimeError("API health failed")
summary=[]
for idx,url in enumerate(URLS,1):
 resolved=get("Resolve",{"url":url})
 typ=resolved.get("entity")
 entity_id=resolved.get("id")
 if typ not in ("Category","Product") or not entity_id:
  raise RuntimeError(f"Could not resolve {url}: {resolved}")
 data=get(f"{typ}/{entity_id}")
 # Full source backup, only in workflow artifact, never committed.
 (out/f"{idx}-{typ.lower()}-{entity_id}.json").write_text(
  json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
 summary.append({"url":url,"entity":typ,"id":entity_id,
  "name":data.get("name",data.get("Name")),
  "metaTitle":data.get("metaTitle",data.get("MetaTitle")),
  "metaDescription":data.get("metaDescription",data.get("MetaDescription"))})
(out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
