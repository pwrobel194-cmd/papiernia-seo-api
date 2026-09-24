import json, os, requests

BASE="https://papiernia.net.pl/papiernia-seo-api/v1"
KEY=os.environ["PAPIERNIA_SEO_API_KEY"]
HEADERS={"X-Papiernia-SEO-Key":KEY}
PRODUCTS=[4885,4937,4898]

for product_id in PRODUCTS:
    r=requests.get(f"{BASE}/ProductPictures/{product_id}",headers=HEADERS,timeout=30)
    r.raise_for_status()
    data=r.json()
    print(json.dumps(data,ensure_ascii=False))
