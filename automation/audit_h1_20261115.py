"""Read-only H1 source audit for 2026-11-15 Ahrefs list.
Do NOT mutate production. Inspect API FullDescription vs rendered HTML.
"""
import os, json, re, html, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT='https://papiernia.net.pl'
PRODUCTS = """
cukierki-dla-gosci-weselnych
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
podziekowanie-na-slub-torebka-z-ciasteczkiem-z-wrozba
""".split()
TOPICS = """
kategorie
poradnik
ile-podziekowan-dla-gosci-zamowic
co-napisać-na-podziekowaniu-dla-gosci
podziekowania-dla-gosci-do-5-zl
jak-wybrac-upominki-dla-gosci-na-chrzest
jak-wybrac-podziekowania-dla-gosci-na-komunie
jak-zaplanowac-podziekowania-na-urodziny
jak-wybrac-upominki-dla-klientow-firmowych
jakie-podziekowania-dla-gosci-weselnych-wybrac
""".split()
assert len(PRODUCTS)==27 and len(TOPICS)==10
KEY=os.environ.get("PAPIERNIA_SEO_API_KEY","")
def get(url,secret=False):
    headers={'Accept':'application/json' if secret else 'text/html',
             'User-Agent':'Mozilla/5.0 (compatible; Papiernia-H1-Audit/1.0)'}
    if secret:
        headers['X-Papiernia-SEO-Key']=KEY
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers), timeout=24) as r:
        return r.read().decode('utf-8','replace')
def headings(s):
    result=[]
    for m in re.finditer(r'<h1\b[^>]*>(.*?)</h1\s*>',s or '',re.I|re.S):
        text=html.unescape(re.sub(r'<[^>]+>','',m.group(1)))
        result.append(' '.join(text.split())[:160])
    return result
def snap_field(d,k):
    if isinstance(d,dict):
        for key,val in d.items():
            if key.lower()==k.lower() and isinstance(val,str):return val
        for val in d.values():
            v=snap_field(val,k)
            if v is not None:return v
    if isinstance(d,list):
        for val in d:
            v=snap_field(val,k)
            if v is not None:return v
    return None
def resolve_id(v):
    if isinstance(v,dict):
        for k in ('ProductId','productId','id','Id','entityId'):
            x=v.get(k)
            if isinstance(x,int) and x>0:return x
        for x in v.values():
            z=resolve_id(x)
            if z:return z
    if isinstance(v,list):
        for x in v:
            z=resolve_id(x)
            if z:return z
    return None
out=[]
for kind,slugs in [('product',PRODUCTS),('topic',TOPICS)]:
    for slug in slugs:
        url=ROOT+'/'+slug
        row={'url':url,'kind':kind}
        try:
            public=get(url)
            row['public_h1']=headings(public)
            row['public_has_personalizowane_upominki']=('Personalizowane upominki' in public)
            if kind=='product':
                path='/papiernia-seo-api/v1/Resolve?'+urllib.parse.urlencode({'url':url})
                resolved=json.loads(get(ROOT+path,True))
                id=resolve_id(resolved)
                if not id: raise ValueError('Resolve returned no product id')
                row['id']=id
                snap=json.loads(get(ROOT+'/papiernia-seo-api/v3/ProductSnapshot/'+str(id),True))
                full=snap_field(snap,'FullDescription') or ''
                short=snap_field(snap,'ShortDescription') or ''
                row['full_description_h1']=headings(full)
                row['short_description_h1']=headings(short)
                row['full_description_has_personalizowane_upominki']=('Personalizowane upominki' in full)
                row['short_description_has_personalizowane_upominki']=('Personalizowane upominki' in short)
                row['full_description_h1_tags_count']=len(headings(full))
                row['short_description_h1_tags_count']=len(headings(short))
            row['ok']=True
        except Exception as exc:
            row['ok']=False
            row['error']=str(exc)[:220]
        out.append(row)
        print(kind,slug,row.get('public_h1'),row.get('full_description_h1'),row.get('error'),flush=True)
report={'mode':'READ_ONLY','products':len(PRODUCTS),'topics':len(TOPICS),'results':out}
p=Path('automation/reports/ahrefs-h1-20261115.json')
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
