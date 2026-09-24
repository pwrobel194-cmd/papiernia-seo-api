import json, os, requests, sys
from pathlib import Path

BASE="https://papiernia.net.pl/papiernia-seo-api/v1"
KEY=os.environ["PAPIERNIA_SEO_API_KEY"]
APPLY=os.getenv("APPLY_ALT","false").lower()=="true"
HEADERS={"X-Papiernia-SEO-Key":KEY,"Content-Type":"application/json"}

cfg=json.loads(Path("automation/alt_actions.json").read_text(encoding="utf-8"))
product_id=int(cfg["productId"])

pics=requests.get(f"{BASE}/ProductPictures/{product_id}",headers=HEADERS,timeout=30)
pics.raise_for_status()
known={int(p["Id"]):p for p in pics.json().get("pictures",[])}

report=[]
for a in cfg["actions"][:5]:
    picture_id=int(a["pictureId"])
    if picture_id not in known:
        report.append({"pictureId":picture_id,"status":"ERROR","error":"picture_not_attached_to_product"})
        continue
    old=known[picture_id].get("AltAttribute")
    new=a["altAttribute"].strip()
    if old==new:
        report.append({"pictureId":picture_id,"status":"NO_CHANGE","old":old,"new":new})
        continue
    payload={"pictureId":picture_id,"altAttribute":new,"reason":a.get("reason","ALT SEO correction")}
    r=requests.put(f"{BASE}/UpdatePictureAlt/{product_id}",headers=HEADERS,params={"dryRun":"false" if APPLY else "true"},json=payload,timeout=30)
    r.raise_for_status()
    report.append({"pictureId":picture_id,"status":"APPLIED" if APPLY else "DRY_RUN","old":old,"new":new,"api":r.json()})

print(json.dumps({"mode":"APPLY" if APPLY else "DRY_RUN","productId":product_id,"results":report},ensure_ascii=False,indent=2))
if any(x["status"]=="ERROR" for x in report):
    sys.exit(2)
