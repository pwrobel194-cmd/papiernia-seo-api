import os, re, json, time, unicodedata, concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://papiernia.net.pl/papiernia-seo-api/v1"
KEY = os.environ["PAPIERNIA_SEO_API_KEY"]
HEAD = {"X-Papiernia-SEO-Key": KEY}
NOTE = '<p><strong>Ważne – samodzielne złożenie:</strong> Produkt dostarczany jest do samodzielnego złożenia. Elementy zestawu należy przygotować i połączyć we własnym zakresie, a personalizowaną etykietę samodzielnie nakleić.</p>'
TARGETS = {
    "lizaki": ("lizak", "swiatecz"),
    "oplatki": ("oplat",),
    "swieczka_serce": ("swiecz", "serc", "swiatecz"),
    "serwetki": ("serwet", "swiatecz"),
    "swiece_pienkowe": ("swiec", "pienkow", "swiatecz"),
}
REPORT = {"generatedAt": datetime.now(timezone.utc).isoformat(), "results": [], "candidates": {}}
def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").replace("ł","l").replace("Ł","L"))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()
def get(id):
    try:
        r=requests.get(f"{BASE}/Product/{id}",headers=HEAD,timeout=12)
        if r.status_code==404:return None
        r.raise_for_status()
        return {k[0].lower()+k[1:]: v for k,v in r.json().items()}
    except Exception as e:
        return {"_error": str(e), "id": id}
def has_note(s):
    x=norm(re.sub(r"<[^>]+>", " ",s or ""))
    return bool(re.search(r"samodzieln.{0,90}(zlozen|zlozyc|skladan)|do samodzielnego zlozenia",x))
def append_note(s):
    s=s or ""
    return s.rstrip()+"\n"+NOTE
def request_put(id,payload,dry):
    r=requests.put(f"{BASE}/UpdateProduct/{id}",headers={**HEAD,"Content-Type":"application/json"},params={"dryRun":str(dry).lower()},json=payload,timeout=30)
    r.raise_for_status()
    return r.json()

def run():
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        found=list(pool.map(get,range(4700,5151)))
    errors=[v for v in found if v and "_error" in v]
    if errors:
        REPORT["errors"]=errors[:10]
        raise RuntimeError(f"Scan failed for {len(errors)} products; no changes made")
    products=[v for v in found if v and not v.get("deleted") and v.get("published")]
    selected={}
    for kind, tokens in TARGETS.items():
        matches=[p for p in products if all(t in norm(p.get("name","")) for t in tokens) and any(t in norm(p.get("name","")) for t in ("swiatecz","swieta","swieta","boze narodzenie","wigil"))]
        if kind == "lizaki":
            matches=[p for p in products if p.get("id")==4963 and "lizak" in norm(p.get("name",""))]
        if kind == "oplatki":
            matches=[p for p in products if p.get("id")==4964 and "oplat" in norm(p.get("name",""))]
        REPORT["candidates"][kind]=[{"id":p.get("id"),"name":p.get("name")} for p in matches]
        if len(matches)!=1:
            REPORT["results"].append({"target":kind,"status":"SKIPPED_AMBIGUOUS_OR_MISSING","count":len(matches)})
        else:
            selected[kind]=matches[0]
    for kind,p in selected.items():
        id=p["id"]
        current=get(id)
        if not current or "_error" in current or current.get("name")!=p.get("name"):
            REPORT["results"].append({"target":kind,"id":id,"status":"SKIPPED_READ_MISMATCH"})
            continue
        payload={"reason":"Doprecyzowanie: produkt do samodzielnego złożenia w krótkim i pełnym opisie"}
        fields=[]
        for field in ("shortDescription","fullDescription"):
            text=current.get(field) or ""
            cleaned=text
            if text.count(NOTE)>1:
                cleaned=text.replace(NOTE,"",text.count(NOTE)-1)
            if not has_note(cleaned):
                if not cleaned.strip():
                    continue
                cleaned=append_note(cleaned)
            if cleaned != text:
                payload[field]=cleaned
                fields.append(field)
        if not fields:
            REPORT["results"].append({"target":kind,"id":id,"status":"NO_CHANGE"})
            continue
        try:
            dry=request_put(id,payload,True)
            if dry.get("ok") is not True:
                raise RuntimeError("dryRun rejected")
            applied=request_put(id,payload,False)
            if applied.get("ok") is not True:
                raise RuntimeError("update rejected")
            verify=get(id)
            if not verify or not all(verify.get(f)==payload[f] for f in fields):
                raise RuntimeError("verification mismatch")
            REPORT["results"].append({"target":kind,"id":id,"status":"APPLIED_VERIFIED","fields":fields})
        except Exception as exc:
            REPORT["results"].append({"target":kind,"id":id,"status":"ERROR","error":str(exc)})
    if any(x["status"]=="ERROR" for x in REPORT["results"]):
        raise RuntimeError("One or more updates failed")

if __name__=="__main__":
    try:run()
    except Exception as e:
        REPORT["fatal"]=str(e)
        raise
    finally:
        Path("reports").mkdir(exist_ok=True)
        path="reports/assembly-notes-2026-10-18.json"
        Path(path).write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps(REPORT,ensure_ascii=False,indent=2))
