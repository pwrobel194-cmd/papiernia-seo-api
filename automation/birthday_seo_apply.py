"""Guarded birthday SEO metadata update. No descriptions, prices or URLs modified."""
import json, os, pathlib, requests, sys
BASE="https://papiernia.net.pl/papiernia-seo-api/v1"
TARGETS=json.loads("[{\"entity\":\"Category\",\"id\":20,\"beforeTitle\":\"Podziękowania dla gości urodziny: 18, 30, 40, 50, 60\",\"beforeDescription\":\"Podziękowania dla gości na urodziny: oryginalne upominki na 18, 30, 40, 50, czy 60 urodziny, które sprawią, że ten dzień będzie niezapomniany\",\"afterTitle\":\"Podziękowania dla gości na urodziny – upominki\",\"afterDescription\":\"Personalizowane podziękowania i drobne upominki dla gości na 18., 30., 40., 50. i 60. urodziny. Odkryj magnesy, słodycze i herbatki z dedykacją.\"},{\"entity\":\"Product\",\"id\":4932,\"beforeTitle\":\"Podziękowania za przybycie na urodziny – z czekoladką\",\"beforeDescription\":\"Personalizowane podziękowania dla gości na urodziny: kartka A6 z mleczną czekoladką i własnym tekstem. Minimum 30 szt., realizacja 2–3 dni.\",\"afterTitle\":\"Kartka z czekoladką – podziękowanie za przybycie na urodziny\",\"afterDescription\":\"Podziękuj za przybycie na urodziny kartką A6 z mleczną czekoladką i własną dedykacją. Personalizowany drobiazg dla gości urodzinowych.\"},{\"entity\":\"Product\",\"id\":4933,\"beforeTitle\":\"Pomysł na oryginalne podziękowania urodzinowe \",\"beforeDescription\":\"Upominek urodzinowy dla gości z herbatką - gotowe pomysły na personalizowane podziękowania urodzinowe dla gości na papiernia.net.pl\",\"afterTitle\":\"Herbatka EKO z etykietą – upominek dla gości na urodziny\",\"afterDescription\":\"Oryginalny upominek dla gości na urodziny: mieszanka herbaty w papierowym opakowaniu EKO z personalizowaną etykietą i dedykacją.\"}]")
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]})
out=pathlib.Path("birthday-seo-deployment")
out.mkdir(exist_ok=True)
report=[]
def get(path):
 r=session.get(f"{BASE}/{path}",timeout=40);r.raise_for_status();return r.json()
def put(path,data,dry):
 r=session.put(f"{BASE}/{path}",params={"dryRun":str(dry).lower()},json=data,timeout=45)
 r.raise_for_status();return r.json()
def save():
 (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
try:
 if not get("Health").get("ok"):raise RuntimeError("API health not OK")
 for t in TARGETS:
  path=f'{t["entity"]}/{t["id"]}'
  old=get(path)
  (out/f'backup-{t["entity"].lower()}-{t["id"]}.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding="utf-8")
  title=old.get("MetaTitle",old.get("metaTitle",""))
  desc=old.get("MetaDescription",old.get("metaDescription",""))
  if (title,desc)==(t["afterTitle"],t["afterDescription"]):
   report.append({"id":t["id"],"status":"already_applied"});save();continue
  if (title,desc)!=(t["beforeTitle"],t["beforeDescription"]):
   raise RuntimeError(f'Unexpected current metadata for {path}; refusing overwrite')
  if old.get("Deleted",old.get("deleted",False)) or not old.get("Published",old.get("published",True)):
   raise RuntimeError(f'{path} not published or deleted')
  change={"metaTitle":t["afterTitle"],"metaDescription":t["afterDescription"],
   "requestId":f'birthday-seo-20261029-{t["entity"].lower()}-{t["id"]}',
   "reason":"Separate category and product search intents; metadata only"}
  test=put(f'Update{t["entity"]}/{t["id"]}',change,True)
  report.append({"id":t["id"],"status":"dry_run_ok","dryRunResult":test});save()
  # Confirm dry-run has not mutated data
  check=get(path)
  if (check.get("MetaTitle",check.get("metaTitle","")),check.get("MetaDescription",check.get("metaDescription","")))!=(title,desc):
   raise RuntimeError(f'Dry-run unexpectedly changed {path}')
  result=put(f'Update{t["entity"]}/{t["id"]}',change,False)
  fresh=get(path)
  if (fresh.get("MetaTitle",fresh.get("metaTitle","")),fresh.get("MetaDescription",fresh.get("metaDescription","")))!=(t["afterTitle"],t["afterDescription"]):
   raise RuntimeError(f'Write verification failed for {path}')
  report[-1]={"id":t["id"],"status":"verified_applied","apiResult":result}
  save()
 print(json.dumps(report,ensure_ascii=False))
except Exception as exc:
 report.append({"status":"failed","error":str(exc)});save();print(str(exc),file=sys.stderr);raise
