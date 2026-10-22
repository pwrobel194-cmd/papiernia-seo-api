"""Targeted, auditable SEO meta update for three distinct fortune-cookie products."""
import json, os, sys, uuid
from pathlib import Path
import requests

BASE = "https://papiernia.net.pl/papiernia-seo-api/v1"
KEY = os.getenv("PAPIERNIA_SEO_API_KEY", "").strip()
if not KEY:
    raise RuntimeError("Missing GitHub Actions secret PAPIERNIA_SEO_API_KEY. Set it under repository Settings > Secrets and variables > Actions.")
S = requests.Session()
S.headers.update({"X-Papiernia-SEO-Key": KEY})
TARGETS = [
  ("https://papiernia.net.pl/ciasteczka-z-wrozba-na-podziekowania",
   "Ciasteczka z wróżbą na wesele – białe pudełeczko",
   "Ciasteczka z wróżbą w białym pudełeczku jako podziękowania dla gości weselnych. Sprawdź dostępne możliwości personalizacji i wybierz upominek na ślub."),
  ("https://papiernia.net.pl/podziekowania-dla-gosci-ciasteczko-z-wrozba",
   "Ciasteczko z wróżbą w pudełeczku kraft – wesele",
   "Rustykalne podziękowania dla gości weselnych: ciasteczko z wróżbą w pudełeczku kraft. Poznaj szczegóły produktu i możliwości personalizacji."),
  ("https://papiernia.net.pl/ciasteczka-z-wrozba-dla-gosci-na-wesele",
   "Ciasteczko z wróżbą i winietka 2w1 na wesele",
   "Ciasteczko z wróżbą i winietka 2w1 na stół weselny. Praktyczne połączenie oznaczenia miejsca i drobnego podziękowania dla gości."),
]
def call(method, path, **kwargs):
    r = S.request(method, BASE+"/"+path, timeout=40, **kwargs)
    if not r.ok:
        raise RuntimeError(f"API {method} {path}: HTTP {r.status_code}; response: {r.text[:350]}")
    try:
        return r.json()
    except ValueError as exc:
        raise RuntimeError(f"API {method} {path}: expected JSON, got {r.text[:200]}") from exc
def getfield(d, k):
    return d.get(k, d.get(k[0].upper()+k[1:], ""))
def main():
    Path("reports").mkdir(exist_ok=True)
    print("Starting targeted SEO update; checking API health", flush=True)
    health = call("GET", "Health")
    if not health.get("ok"):
        raise RuntimeError(f"API Health returned unhealthy response: {str(health)[:200]}")
    backups = []
    for url, title, description in TARGETS:
        print("Resolving:", url, flush=True)
        resolved = call("GET", "Resolve", params={"url":url})
        if resolved.get("entity") != "Product" or not resolved.get("id"):
            raise RuntimeError("Product resolution failed: "+url)
        pid = resolved["id"]
        original = call("GET", "Product/"+str(pid))
        backups.append({"url":url, "id":pid, "original":original,
                        "proposed":{"metaTitle":title,"metaDescription":description}})
    Path("reports").mkdir(exist_ok=True)
    out = Path("reports/fortune-cookie-before-after.json")
    out.write_text(json.dumps(backups, ensure_ascii=False, indent=2), encoding="utf-8")
    # Validate all updates first; no writes until every dry-run succeeds.
    for b in backups:
        proposed = b["proposed"]
        payload = {**proposed, "requestId":"cookie-check-"+str(uuid.uuid4()),
                   "reason":"Rozdzielenie intencji SEO trzech produktów"}
        call("PUT", "UpdateProduct/"+str(b["id"]), params={"dryRun":"true"}, json=payload)
    for b in backups:
        payload = {**b["proposed"], "requestId":"cookie-apply-"+str(uuid.uuid4()),
                   "reason":"Rozdzielenie intencji SEO trzech produktów"}
        b["result"] = call("PUT", "UpdateProduct/"+str(b["id"]),
                           params={"dryRun":"false"}, json=payload)
        current = call("GET", "Product/"+str(b["id"]))
        if getfield(current,"metaTitle") != b["proposed"]["metaTitle"] or getfield(current,"metaDescription") != b["proposed"]["metaDescription"]:
            raise RuntimeError("Verification failed: "+b["url"])
        b["verified"] = True
        out.write_text(json.dumps(backups, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Verified updates:",len(backups))
if __name__ == "__main__":
    main()
