import json, os, requests
from pathlib import Path

BASE="https://papiernia.net.pl/papiernia-seo-api/v1"
KEY=os.environ["PAPIERNIA_SEO_API_KEY"]
HEADERS={"X-Papiernia-SEO-Key":KEY}
URL="https://papiernia.net.pl/lizaki-swiateczne"

def get(path, params=None):
    r=requests.get(f"{BASE}/{path}",headers=HEADERS,params=params,timeout=30)
    r.raise_for_status()
    return r.json()

health=get("Health")
resolved=get("Resolve",{"url":URL})
if resolved.get("entity")!="Product":
    raise RuntimeError(f"Unexpected entity: {resolved}")
pid=int(resolved["id"])
product=get(f"Product/{pid}")
pictures=get(f"ProductPictures/{pid}")

print("HEALTH="+json.dumps(health,ensure_ascii=False))
print("RESOLVED="+json.dumps(resolved,ensure_ascii=False))
print("PRODUCT="+json.dumps(product,ensure_ascii=False))
print("PICTURES="+json.dumps(pictures,ensure_ascii=False))

Path("reports").mkdir(exist_ok=True)
Path("reports/lizaki-swiateczne-before.json").write_text(
    json.dumps({"health":health,"resolved":resolved,"product":product,"pictures":pictures},ensure_ascii=False,indent=2),
    encoding="utf-8"
)
Path("reports/lizaki-swiateczne-before.html").write_text(product.get("FullDescription") or "",encoding="utf-8")
