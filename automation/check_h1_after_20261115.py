import concurrent.futures, datetime, html, json, re, urllib.request
from pathlib import Path
slugs = """cukierki-dla-gosci-weselnych
mini-prezenciki-dla-klientek-herbatki-na-boze-narodzenie
magnesy-dla-gosci-na-wesele
swieczki-prezent-dla-gosci-weselnych
ciasteczka-z-wrozba-wesele
swieczki-dla-gosci-weselnych-podziekowanie-na-slub
tani-upominek-dla-klientow-na-swieta
upominek-swiateczny-dla-klientow
prezenciki-dla-klientow-na-swieta-bozego-narodzenia
kartki-swiateczne-dla-firm
magnes-drobiazg-na-swieta-dla-klientow
lizaki-reklamowe-z-nadrukiem-logo-upominek-na-swieta
zyczenia-dla-klientow-prezenciki-upominek-swieta-bozego-narodzenia
kartki-swiateczne-z-logo-z-zyczeniami-dla-klientow
oryginalny-prezent-dla-klientow-upominek-swiateczny
ciasteczka-z-wrozba-na-podziekowania
podziekowania-dla-gosci-ciasteczko-z-wrozba
magnesy-na-weselne
czekoladki-na-wesele
czekoladki-slubne-dla-gosci
podziekowania-dla-gosci-z-winietka
ciasteczka-z-wrozba-slub
zdrapki-dla-gosci-weselnych
swieczki-na-prezent-dla-gosci-weselnych
czekoladka-dla-gosci-weselnych
herbata-upominek-dla-gosci-na-wesele
podziekowanie-na-slub-torebka-z-ciasteczkiem-z-wrozba""".split()
def inspect(slug):
    url="https://papiernia.net.pl/"+slug
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; Papiernia-H1-QA/1.0)","Cache-Control":"no-cache","Pragma":"no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=22) as r:
            raw=r.read().decode("utf-8","replace")
            status=r.status
        h1=[" ".join(html.unescape(re.sub(r"<[^>]+>","",m.group(1))).split()) for m in re.finditer(r"<h1\b[^>]*>(.*?)</h1\s*>",raw,re.I|re.S)]
        h2=[" ".join(html.unescape(re.sub(r"<[^>]+>","",m.group(1))).split()) for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2\s*>",raw,re.I|re.S)]
        return {"url":url,"status":status,"h1":h1,"h2_personalizowane":any(s.strip().lower()=="personalizowane upominki" for s in h2),"raw_personalizowane":len(re.findall("Personalizowane upominki",raw,re.I))}
    except Exception as e: return {"url":url,"error":str(e)[:250]}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    results=list(ex.map(inspect,slugs))
report={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"mode":"read_only","count":len(results),"results":results}
Path("automation/reports/ahrefs-h1-after-fix-20261115.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for x in results: print(x.get("url","").split("/")[-1], len(x.get("h1",[])), x.get("h2_personalizowane"),x.get("error",""), flush=True)
