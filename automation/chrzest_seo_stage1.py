"""Chrzest SEO phase 1. Existing Papiernia API v3, safe preview/commit with readback.
Default mode is preview (POST only). Mode apply is exclusively for explicit approved workflow.
No URL, SKU, prices, publish, gallery or image alterations.
"""
import os, json, re, hashlib, pathlib, requests, sys
BASE="https://papiernia.net.pl/papiernia-seo-api"
SECRET=os.environ["PAPIERNIA_SEO_API_KEY"]
MODE=os.environ.get("SEO_MODE","preview").lower()
if MODE not in ("preview","apply"): raise RuntimeError("Bad mode")
s=requests.Session()
s.headers.update({"X-Papiernia-SEO-Key":SECRET,"Accept":"application/json"})
OUT=pathlib.Path("audit/chrzest-stage1");OUT.mkdir(parents=True,exist_ok=True)
TARGETS=[
 {"id":19,"kind":"Category","url":"https://papiernia.net.pl/chrzest","sha":"e72357a34bac1c8a95753225d83ff01049eabfdcd60f096e29709ed1bae85724",
  "titleSha":"d5054a0ec10f427139857cbace5f5fbf9c7835fe097a3a43d83a356a5ed4e44f"},
 {"id":4929,"kind":"Product","url":"https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest","sha":"b23ec28542e2e5a3af80eaeb9249614ad83b1bc92c7952e3222a3e117fb9de95",
  "titleSha":"5a2684b6590f05f3df3cb9048f90d2aa7133bb9ef028964a56452c79dc3454c4"},
 {"id":4930,"kind":"Product","url":"https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest","sha":"f4e6a02e89a0cc95539a46a6d74bbebe06432dbe7e5f04f01aab818ed89d40a6",
  "titleSha":"0514b2c1271d307e15a4ae45e41aee1535acc98f96632c817c2d16b38b1db6a3"}
]
def hash_of(text):return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
def field(obj,name):return obj.get(name,obj.get(name[0].upper()+name[1:]))
def get(path,params=None):
 r=s.get(BASE+path,params=params,timeout=40);r.raise_for_status();return r.json()
def snapshot(t):
 r=get(f"/v3/{t['kind']}Snapshot/{t['id']}")
 return r.get("data",r.get("snapshot",r))
def once(s,old,new):
 count=s.count(old)
 if count!=1:raise RuntimeError(f"Exact source match count {count}, expected 1: {old[:90]}")
 return s.replace(old,new,1)
def img_tags(x):return re.findall(r"<img\b[^>]*>",x,re.I)
def anchor_tags(x):return re.findall(r"<a\b[^>]*>",x,re.I)
def protected_in_order(before,after):
 iterator=iter(after)
 return all(any(item==expected for item in iterator) for expected in before)
def call(method,path,payload):
 r=getattr(s,method)(BASE+"/v3/"+path,json=payload,timeout=55)
 r.raise_for_status()
 val=r.json()
 if val.get("ok") is False or val.get("success") is False:
  raise RuntimeError("API indicated failure for "+path)
 return val
def prep(t,cur):
 id=t["id"]
 key="description" if t["kind"]=="Category" else "fullDescription"
 original=field(cur,key) or ""
 if hash_of(original)!=t["sha"]:raise RuntimeError(f"Source HTML changed for {id}")
 if hash_of(field(cur,"metaTitle"))!=t["titleSha"]:raise RuntimeError(f"Source title changed for {id}")
 resolved=get("/v1/Resolve",{"url":t["url"]})
 if str(field(resolved,"id"))!=str(id) or str(field(resolved,"entity")).lower()!=t["kind"].lower():
  raise RuntimeError(f"Unexpected URL mapping for {id}")
 h=original
 if id==19:
  meta={
    "metaTitle":"Podziękowania dla gości na Chrzest – upominki | Papiernia",
    "metaDescription":"Podziękowania dla gości na Chrzest Święty: personalizowane świeczki i herbatki w opakowaniach EKO. Wybierz wzór i dedykację na chrzciny."}
  h=once(h,
   "<p>Narodziny dziecka to zawsze ogromne wydarzenie w życiu każdej rodziny a chrzest święty staje się jednym z pierwszych i najważniejszych momentów w ich życiu Upominki dla gości na przyjęciu z okazji Chrztu Świętego to coraz częściej spotykany zwyczaj jako podziękowanie za przybycie zaproszonych gości. Drobny prezencik położony na stole przy każdym nakryciu to nie tylko miły akcent na przyjęciu, ale też dodatkowa dekoracja stołu</p>",
   "<p>Narodziny dziecka to szczególne wydarzenie w życiu rodziny, a Chrzest Święty jest jednym z pierwszych ważnych momentów wspólnego świętowania. Personalizowane podziękowania dla gości na Chrzest pozwalają wyrazić wdzięczność bliskim za obecność podczas uroczystości. Drobne upominki na chrzciny można ułożyć przy każdym nakryciu albo wręczyć po przyjęciu – będą jednocześnie miłym gestem, dekoracją stołu i pamiątką z tego dnia.</p>")
  h=once(h,"Starannie dobrany prezent dla gości chrzest podkreśla rangę uroczystości",
            "Starannie dobrany upominek dla gości na Chrzest podkreśla rangę uroczystości")
  h=once(h,"jaki prezent dla gości chrzest wybrać","jakie podziękowania dla gości na Chrzest wybrać")
  h=once(h,"Cały proces przygotowania personalizacji, w liczony jest w cenę produktu.",
            "Przygotowanie personalizacji jest wliczone w cenę produktu.")
  h=once(h,"<h2>Upominki z herbatką na Chrzciny</h2>",
   '<h2>Herbatki na Chrzest – personalizowane upominki dla gości</h2>\r\n'
   '<p>Jeżeli szukasz praktycznego, drobnego upominku na chrzciny, zobacz <a href="https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest" title="Herbatki na Chrzest dla gości">herbatki na Chrzest z personalizowaną etykietą</a>. Naturalne opakowanie EKO i własna dedykacja pasują zarówno do uroczystości dziewczynki, jak i chłopca.</p>')
  h=once(h,"<h2>Świeczki podziękowania na Chrzest</h2>",
   '<h2>Świeczki na Chrzest – podziękowania dla gości</h2>\r\n'
   '<p>Alternatywą dla herbatki są <a href="https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest" title="Świeczki w opakowaniu EKO na Chrzest">świeczki na Chrzest w opakowaniu EKO</a> z personalizowanym bilecikiem. To elegancki, nieduży prezencik dla gości na chrzciny.</p>')
  # Roczek is supporting intent, move intact below both product sections.
  start="<h2>Podziękowania na roczek dla gości</h2>"
  end="<h2>Oferta podziękowań dla gości na chrzest</h2>"
  i=h.find(start);j=h.find(end)
  if not (0<=i<j):raise RuntimeError("Roczek section layout changed")
  roczek=h[i:j]
  if img_tags(roczek) or anchor_tags(roczek):raise RuntimeError("Unexpected media/links in roczek segment")
  h=h[:i]+h[j:]
  marker="<h2>Upominki dla gości na chrzest roczek - szybka realizacja</h2>"
  h=once(h,marker,roczek+'<h2>Jak zamówić podziękowania na Chrzest?</h2>\r\n'
     '<p>Wybierz świeczkę lub herbatkę, a następnie model graficzny i tekst na etykietę. Podczas zamówienia podaj imię dziecka, datę Chrztu Świętego oraz wybrane podziękowanie dla gości. Jeżeli nie masz gotowego tekstu, możesz wybrać krótką, klasyczną dedykację.</p>\r\n'
     '<h3>Co napisać na podziękowaniu dla gości na Chrzest?</h3>\r\n'
     '<p>Możesz użyć prostego tekstu, na przykład: „Dziękujemy za obecność w dniu mojego Chrztu Świętego” i dodać imię dziecka oraz datę uroczystości. Taka dedykacja sprawdzi się zarówno na etykiecie herbatki, jak i na bileciku przy świeczce.</p>\r\n'
     '<h3>Kiedy wręczyć upominki na chrzciny?</h3>\r\n'
     '<p>Podziękowania na Chrzest możesz ułożyć przy nakryciach, aby były częścią dekoracji stołu, albo wręczyć bliskim na zakończenie spotkania. W obu przypadkach personalizowany drobiazg przypomni o wspólnie spędzonym dniu.</p>\r\n'
     '<p>Więcej porad znajdziesz w artykule <a href="https://papiernia.net.pl/jak-wybrac-upominki-dla-gosci-na-chrzest" title="Jak wybrać upominki dla gości na Chrzest">jak wybrać upominki dla gości na Chrzest</a>.</p>\r\n'
     +marker)
  h=once(h,"<p>Średni czas realizacji upominków na uroczystość chrztu świętego, przygotowujemy średnio w ciągu 3 dni roboczych.</p>",
          "<p>Upominki na uroczystość Chrztu Świętego przygotowujemy średnio w ciągu 3 dni roboczych. Aktualny termin potwierdzamy przy zamówieniu.</p>")
 if id==4929:
  meta={
   "name":"Świeczka na Chrzest w opakowaniu EKO – podziękowanie dla gości",
   "metaTitle":"Świeczka na Chrzest z personalizacją | Papiernia",
   "metaDescription":"Świeczka na Chrzest w opakowaniu EKO z bilecikiem i własnym tekstem. Personalizowane podziękowanie dla gości na chrzciny, dla dziewczynki i chłopca."}
  h=once(h,
   '<h3 class="" style="text-align: center;" data-start="0" data-end="44">Świeczki – Upominki na Chrzest dla Gości</h3>',
   '<h2 class="" style="text-align: center;" data-start="0" data-end="44">Świeczka na Chrzest w opakowaniu EKO – podziękowanie dla gości</h2>')
  h=once(h,
   "Szukasz wyjątkowego sposobu na podziękowanie gościom za ich obecność na Chrzcie? Świeczki to idealny wybór - prezenciki dla przybyłych gości na przyjęcie z okazji Chrztu Świętego to doskonały pomysł, aby w oryginalny sposób podziękować im za obecność w tak ważnym dniu. Nasza oferta obejmuje szeroką gamę gotowych drobnych upominków, które można dostosować do charakteru Twojej uroczystości.",
   "Biała świeczka w brązowym opakowaniu EKO z personalizowanym bilecikiem to elegancki sposób, aby podziękować bliskim za przybycie na Chrzest Święty dziecka. Taki drobny upominek dla gości na chrzciny możesz ułożyć przy nakryciu lub wręczyć po przyjęciu. Na etykiecie umieścimy imię dziecka, datę uroczystości i krótką dedykację, dzięki czemu świeczka stanie się osobistą pamiątką.")
  h=once(h,"Personalizowane Upominki na Chrzest</h3>","Personalizowane świeczki na Chrzest – etykieta z dedykacją</h3>")
  h=once(h,
   "Nasza oferta obejmuje szeroką gamę upominków, które można dostosować do charakteru Twojej uroczystości. Dodatkowo, bez dodatkowych kosztów oferujemy możliwość personalizacji – na upomoinkach można umieścić imię dziecka, datę uroczystości i krótkie podziękowanie, co sprawia, że każdy gość poczuje się wyjątkowo otrzymująć unikalne i jedyny w swoim rodzaju upominek.",
   "Personalizacja bilecika jest wliczona w cenę upominku. Możesz podać imię dziecka, datę Chrztu Świętego i własny tekst podziękowania albo wybrać jeden z dostępnych wzorów. Etykieta w formacie 6,3 × 6,3 cm dołączona do brązowego opakowania EKO nadaje świeczce osobisty charakter.")
  h=once(h,"Wyjątkowe Podziękowania na Chrzest</h3>","Dlaczego świeczka to dobry upominek na Chrzest?</h3>")
  h=once(h,
   '<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą ofertą personalizowanych upominków na Chrzest: Ciasteczka z wróżbą, słodkie upominki, kartki z czekoladką, magnesy, herbatki i wiele innych. Więcej propozycji prezentów na Chrcini i roczek, w katetogorii -<a title="Podziękowania i upominki na chrzciny " href="https://papiernia.net.pl/chrzest"><strong>"Podziękowania dla gości na Crzest"</strong></a></p>',
   '<p style="text-align: center;">Szukasz innego podziękowania dla gości na Chrzciny? Zobacz także <a href="https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest" title="Herbatka na Chrzest dla gości">herbatkę na Chrzest w opakowaniu EKO</a> albo przejrzyj kategorię <a title="Podziękowania i upominki na chrzciny " href="https://papiernia.net.pl/chrzest"><strong>podziękowania dla gości na Chrzest</strong></a>.</p>')
 if id==4930:
  meta={"name":"Herbatka na Chrzest – personalizowane podziękowanie dla gości"}
  h=once(h,
    '<h2 style="text-align: center;">Herbatka dla gości na Chrzest – personalizowane podziękowanie</h2>',
    '<h2 style="text-align: center;">Herbatka na Chrzest w opakowaniu EKO – upominek dla gości</h2>')
  h=once(h,
   '<p style="text-align: center;">W naszej ofercie znajdziesz również inne personalizowane prezenty przygotowane specjalnie na Chrzest Święty. Są to między innymi ciasteczka z wróżbą, słodkie upominki, kartki z czekoladką, magnesy, herbatki oraz inne drobiazgi, które możesz dopasować do charakteru przyjęcia.</p>',
   '<p style="text-align: center;">Jeśli szukasz innej formy podziękowania dla gości na Chrzest Święty, sprawdź również <a href="https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest" title="Świeczka EKO na Chrzest">świeczkę na Chrzest w opakowaniu EKO</a>. Obydwa upominki można dopasować do uroczystości dziecka dzięki personalizowanemu bilecikowi.</p>')
  h=once(h,
    'Znajdziesz tam różne propozycje prezentów na Chrzciny dla dziewczynki i chłopca.',
    'Znajdziesz tam obecnie dwie formy podziękowań dla gości na Chrzciny – świeczki i herbatki – w wersjach dla dziewczynki i chłopca.')
 else: pass
 if h==original:raise RuntimeError("HTML unexpectedly unchanged")
 if img_tags(original)!=img_tags(h):raise RuntimeError("HTML image integrity failed")
 if not protected_in_order(anchor_tags(original),anchor_tags(h)):
  # Allowed ONE original anchor modification in ID 4929 to fix typo; old href still protected below.
  if id!=4929:raise RuntimeError("Preexisting anchor tags altered")
  oldhref=re.findall(r'<a\b[^>]*\bhref="([^"]+)"',original,re.I)
  newhref=re.findall(r'<a\b[^>]*\bhref="([^"]+)"',h,re.I)
  if not protected_in_order(oldhref,newhref):raise RuntimeError("Preexisting href lost")
 else: pass
 meta[key]=h
 meta["reason"]="Chrzest SEO stage 1: occasion-focused H1 and metadata, preserve media, contextual links"
 return meta,original,h
def save(report,file):
 (OUT/file).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def main():
 staged=[]
 for t in TARGETS:
  cur=snapshot(t)
  payload,old,new=prep(t,cur)
  result=call("post",f"Preview{t['kind']}Seo/{t['id']}",payload)
  if result.get("dryRun") is not True:raise RuntimeError("Preview not confirmed dry-run")
  token=result.get("approvalToken",result.get("ApprovalToken"))
  if not token:raise RuntimeError("Preview did not issue approval token")
  staged.append((t,cur,payload,old,new,token))
  print(json.dumps({"id":t["id"],"status":"PREVIEW_OK","fields":[k for k in payload if k not in ("reason","description","fullDescription")],
     "beforeHTMLLength":len(old),"afterHTMLLength":len(new),
     "sameImages":len(img_tags(old)),"linksBefore":len(anchor_tags(old)),"linksAfter":len(anchor_tags(new))},ensure_ascii=False))
 report=[]
 if MODE=="preview":
  for t,cur,payload,old,new,_ in staged:
   report.append({"id":t["id"],"url":t["url"],"status":"PREVIEW_OK",
    "fields":[k for k in payload if k!="reason"],"beforeHtmlSha256":hash_of(old),
    "afterHtmlSha256":hash_of(new),"htmlLengthBefore":len(old),"htmlLengthAfter":len(new),
    "imageCountPreserved":len(img_tags(old)),"linksBefore":len(anchor_tags(old)),
    "linksAfter":len(anchor_tags(new)),
    "before":{k:field(cur,k) for k in ("name","metaTitle","metaDescription")},
    "after":{k:payload.get(k,field(cur,k)) for k in ("name","metaTitle","metaDescription")}})
  save(report,"preview.json")
  return
 for t,cur,payload,old,new,token in staged:
  result={"id":t["id"],"url":t["url"],"status":"COMMIT_ATTEMPTED"}
  report.append(result);save(report,"applied.json")
  try:
   call("put",f"Commit{t['kind']}Seo/{t['id']}",{**payload,"approvalToken":token})
   after=snapshot(t)
   for k,v in payload.items():
    if k=="reason":continue
    if field(after,k)!=v:raise RuntimeError(f"Readback mismatched {t['id']} field={k}")
   key="description" if t["kind"]=="Category" else "fullDescription"
   assert field(after,key)==new
   for x in ("metaKeywords","sku","published","deleted","seName"):
    if field(after,x)!=field(cur,x):raise RuntimeError(f"Unrequested field changed {x} on {t['id']}")
   if t["kind"]=="Product" and field(after,"shortDescription")!=field(cur,"shortDescription"):
    raise RuntimeError("Unexpected short description change")
   if img_tags(field(after,key))!=img_tags(old):raise RuntimeError("An image tag was altered")
   resolved=get("/v1/Resolve",{"url":t["url"]})
   if str(field(resolved,"id"))!=str(t["id"]):raise RuntimeError("Public URL mapping changed after write")
   result.update({"status":"APPLIED_VERIFIED","before":{x:field(cur,x) for x in ("name","metaTitle","metaDescription")},
      "after":{x:field(after,x) for x in ("name","metaTitle","metaDescription")},
      "oldHtmlSha256":hash_of(old),"newHtmlSha256":hash_of(new),"imagesPreserved":len(img_tags(old)),
      "linksBefore":len(anchor_tags(old)),"linksAfter":len(anchor_tags(new))})
   save(report,"applied.json")
   print(json.dumps({"id":t["id"],"status":"APPLIED_VERIFIED","images":len(img_tags(old)),
     "linksBefore":len(anchor_tags(old)),"linksAfter":len(anchor_tags(new))},ensure_ascii=False))
  except Exception as e:
   result.update({"status":"ERROR","error":str(e)[:400]});save(report,"applied.json")
   raise
if __name__=="__main__":main()
