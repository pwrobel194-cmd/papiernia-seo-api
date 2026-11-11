import os,json,pathlib,requests
from datetime import datetime,timezone
ROOT="https://papiernia.net.pl/papiernia-seo-api/v3"
S=requests.Session();S.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]})
MODE=os.environ.get("SEO_ACTION","preview");assert MODE in ("preview","apply")
REASON="Zlecone przez właściciela 2026-11-11: uzupełnienie ALT i Title głównych zdjęć podkategorii ciasteczek weselnych"
ROWS=[
 ("category",362,5365,"Ciasteczka z wróżbą na wesele – personalizowane podziękowania dla gości","Ciasteczka z wróżbą na wesele | Papiernia"),
 ("product",4904,5423,"Ciasteczko z wróżbą i winietką 2w1 – podziękowanie dla gości weselnych","Ciasteczko z wróżbą i winietką na wesele"),
 ("product",4884,5172,"Ciasteczko z wróżbą w personalizowanej torebce na wesele","Ciasteczko z wróżbą w torebce weselnej"),
 ("product",4898,5352,"Ciasteczko z wróżbą w białym pudełeczku na wesele","Ciasteczko z wróżbą – białe pudełeczko"),
 ("product",4899,5364,"Ciasteczko z wróżbą w pudełeczku EKO – upominek weselny","Ciasteczko z wróżbą w pudełku EKO"),
 ("product",4888,5220,"Różowe pudełeczko ze złotymi kropkami z ciasteczkiem z wróżbą","Ciasteczko z wróżbą – różowe pudełeczko"),
 ("product",4900,5379,"Ciasteczko z wróżbą ze złotym bilecikiem – podziękowanie na ślub","Ciasteczko z wróżbą i złoty bilecik")
]
out=pathlib.Path("reports/wesele-cookies-picture-alt");out.mkdir(parents=True,exist_ok=True)
report={"mode":MODE,"timestamp":datetime.now(timezone.utc).isoformat(),"results":[]}
def api(method,route,body=None):
 r=S.request(method,ROOT+route,json=body,timeout=45)
 if not r.ok:raise RuntimeError(f"{method} {route} {r.status_code}: {r.text[:300]}")
 j=r.json()
 if not j.get("ok"):raise RuntimeError("API returned not ok")
 return j

# Main gallery image only; leave all other images untouched.
for scope,eid,pid,alt,title in ROWS:
 snap=api("GET",f"/{ 'CategorySnapshot' if scope=='category' else 'ProductSnapshot' }/{eid}")
 if scope=="category":
  assert snap["PictureId"]==pid
  before=snap["picture"]
 else:
  matches=[x for x in snap["pictures"] if x["Id"]==pid]
  assert matches and snap["pictures"][0]["Id"]==pid
  before=matches[0]
 if before.get("AltAttribute")==alt and before.get("TitleAttribute")==title:
  report["results"].append({"scope":scope,"id":eid,"pictureId":pid,"status":"already_updated"})
  continue
 payload={"scope":scope,"pictureId":pid,"altAttribute":alt,"titleAttribute":title}
 planned=api("POST",f"/PreviewPictureMetadata/{eid}",payload)
 assert planned.get("dryRun") and planned.get("approvalToken") and planned["after"]["Id"]==pid
 entry={"scope":scope,"id":eid,"pictureId":pid,"before":{"alt":before.get("AltAttribute"),"title":before.get("TitleAttribute")},"after":{"alt":alt,"title":title},"status":"preview_ok"}
 if MODE=="apply":
  applied=api("PUT",f"/CommitPictureMetadata/{eid}",{**payload,"approvalToken":planned["approvalToken"],"reason":REASON})
  assert applied.get("committed")
  updated=api("GET",f"/{ 'CategorySnapshot' if scope=='category' else 'ProductSnapshot' }/{eid}")
  check=updated["picture"] if scope=="category" else [x for x in updated["pictures"] if x["Id"]==pid][0]
  assert check["AltAttribute"]==alt and check["TitleAttribute"]==title
  if scope=="product":
   assert [p["Id"] for p in updated["pictures"]]==[p["Id"] for p in snap["pictures"]]
  entry["status"]="committed_verified"
 report["results"].append(entry)
 (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("PICTURE_RESULT",scope,eid,pid,entry["status"],flush=True)
print("COMPLETE",MODE,len(report["results"]))
