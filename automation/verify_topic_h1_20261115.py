"""One-time read-only check of nine edited nopCommerce Topics.
No API secrets, no writes to store.
"""
import concurrent.futures, html, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLUGS = [
    "poradnik",
    "ile-podziekowan-dla-gosci-zamowic",
    "co-napisac-na-podziekowaniu-dla-gosci",
    "podziekowania-dla-gosci-do-5-zl",
    "jak-wybrac-upominki-dla-gosci-na-chrzest",
    "jak-wybrac-podziekowania-dla-gosci-na-komunie",
    "jak-zaplanowac-podziekowania-na-urodziny",
    "jak-wybrac-upominki-dla-klientow-firmowych",
    "jakie-podziekowania-dla-gosci-weselnych-wybrac",
]
BASE="https://papiernia.net.pl/"
def fetch(slug):
    url=BASE+slug
    record={"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; Papiernia-H1-Verification/1.0)", "Cache-Control":"no-cache","Pragma":"no-cache"})
        with urllib.request.urlopen(req,timeout=30) as resp:
            page=resp.read().decode("utf-8","replace")
            record["http_status"]=resp.status
        def headings(tag):
            return [" ".join(html.unescape(re.sub(r"<[^>]+>","",m.group(1))).split()) for m in re.finditer(fr"<{tag}\b[^>]*>(.*?)</{tag}\s*>",page,re.I|re.S)]
        record["h1"]=headings("h1")
        record["h1_count"]=len(record["h1"])
        record["h2"]=headings("h2")
        record["ok"]=record["h1_count"]==1
    except Exception as e:
        record["error"]=str(e)[:280]
        record["ok"]=False
    return record
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    rows=list(ex.map(fetch,SLUGS))
report={"mode":"read_only","checked_at_utc":datetime.now(timezone.utc).isoformat(),"pages":rows,
  "total":len(rows),"single_h1":sum(v["ok"] for v in rows),"still_multiple_h1":[v["url"] for v in rows if v.get("h1_count",0)>1],
  "http_errors":[v["url"] for v in rows if v.get("error")]}
path=Path("automation/reports/ahrefs-topic-h1-verified-20261115.json")
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Single H1:", report["single_h1"],"/",report["total"])
for v in rows:
    print(v["url"], "H1=", v.get("h1_count"),"OK=",v["ok"],"error=",v.get("error"),flush=True)
