"""SEO Chrzest, 9 Nov 2026: guarded v3 preview/commit, 3 entities.
Default PREVIEW only. Production APPLY is enabled only by separate deployment workflow.
No deletion or reordering of images; full category text preserved and expanded.
"""
import os,re,sys,json,pathlib,hashlib,requests
BASE="https://papiernia.net.pl/papiernia-seo-api"
MODE=os.environ.get("SEO_MODE","preview").lower()
if MODE not in ("preview","apply"):raise RuntimeError("Invalid SEO_MODE")
urls={19:("Category","https://papiernia.net.pl/chrzest"),
4929:("Product","https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest"),
4930:("Product","https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest")}
expected={
19:("e72357a34bac1c8a95753225d83ff01049eabfdcd60f096e29709ed1bae85724","7d54c54eb398bbde34baa4026136f17f4fb1f8cc668181b0a22c1081f3dda681","d5054a0ec10f427139857cbace5f5fbf9c7835fe097a3a43d83a356a5ed4e44f","30673f3c531c35c7309a5cf3efe7ea72a59160fb6002526f77405b18f6b6b5c0"),
4929:("b23ec28542e2e5a3af80eaeb9249614ad83b1bc92c7952e3222a3e117fb9de95","661326088e177b21e60bb7546032c8618106d7bc9536e89946546518fa6ee9eb","5a2684b6590f05f3df3cb9048f90d2aa7133bb9ef028964a56452c79dc3454c4","01502fababea79a07fcf31c2fb03741d7e2ad8b3d8dcb665420e918bced10cfb"),
4930:("f4e6a02e89a0cc95539a46a6d74bbebe06432dbe7e5f04f01aab818ed89d40a6","9836f4199ad752d67a94c4318e8d7e78f3ff8f0124ddee45f651ad0057ca654a","0514b2c1271d307e15a4ae45e41aee1535acc98f96632c817c2d16b38b1db6a3","dbc5402c503077e53c6cb2d746f20a9b953b55fc4ee71c92ee6922335ecb0ac1")}
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"],"Accept":"application/json"})
out=pathlib.Path("audit/chrzest-20261109");out.mkdir(parents=True,exist_ok=True)
def sha(x):return hashlib.sha256((x or "").encode("utf-8")).hexdigest()
def field(d,k):return d.get(k,d.get(k[0].upper()+k[1:]))
def api(method,path,**kwargs):
 r=getattr(session,method)(BASE+path,timeout=55,**kwargs)
 r.raise_for_status();d=r.json()
 if d.get("ok") is False or d.get("success") is False:raise RuntimeError("API negative: "+path)
 return d
def check_url(id):
 typ,url=urls[id]
 d=api("get","/v1/Resolve",params={"url":url})
 if str(field(d,"entity")).lower()!=typ.lower() or str(field(d,"id"))!=str(id):
  raise RuntimeError("Unexpected public URL mapping: "+str(id))
def snap(id):
 typ,_=urls[id];d=api("get",f"/v3/{typ}Snapshot/{id}")
 obj=d.get("data",d.get("snapshot",d))
 if not isinstance(obj,dict):raise RuntimeError("Unexpected snapshot object")
 return obj
def replace(s,a,b):
 if s.count(a)!=1:raise RuntimeError("Source phrase not unique/missing: "+a[:90])
 return s.replace(a,b,1)
def imgtags(s):return re.findall(r"<img\b[^>]*>",s,flags=re.I)
def links(s):return re.findall(r"<a\b[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"]",s,flags=re.I)
def preserve_links(before,after):
 b=links(before);a=links(after);i=0
 for url in b:
  while i<len(a) and a[i]!=url:i+=1
  if i==len(a):raise RuntimeError("Existing link lost or reordered: "+url)
  i+=1
def change(id,obj):
 kind="description" if id==19 else "fullDescription"
 old=field(obj,kind) or "";text=old
 payload={"reason":"SEO Chrzest 2026-11-09 approved: occasion-led H1, preserved media & URLs"}
 if id==19:
  payload.update({"metaTitle":"Podziękowania dla gości na Chrzest – upominki | Papiernia",
   "metaDescription":"Podziękowania dla gości na Chrzest Święty: personalizowane świeczki i herbatki EKO. Wybierz wzór, dodaj dedykację i zamów upominki na chrzciny od 30 sztuk."})
  # Move existing secondary roczek section below offerings; keep its old text literally.
  m=re.search(r"<h2>Podziękowania na roczek dla gości</h2>.*?(?=<h2>Oferta podziękowań dla gości na chrzest</h2>)",text,re.S)
  if not m:raise RuntimeError("Roczek section not found")
  roczek=m.group(0);text=replace(text,roczek,"")
  text=replace(text,"<h2>Upominki dla gości na chrzest roczek - szybka realizacja</h2>",
               roczek+"<h2>Upominki dla gości na chrzest roczek - szybka realizacja</h2>")
  text=replace(text,"<h2>Podziękowania za przybycie na chrzest</h2>",
   '<h2>Podziękowania za przybycie na chrzest</h2>\r\n'
   '<p>Jeżeli organizujesz przyjęcie po Chrzcie Świętym, wybierz <strong>podziękowania dla gości na Chrzest</strong>, które pasują do dekoracji stołu i pozwalają przekazać osobistą dedykację. Obecnie proponujemy dwa rodzaje upominków: <a href="https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest">świeczki na Chrzest w oprawie EKO</a> oraz <a href="https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest">herbatki na Chrzciny z personalizowaną etykietą</a>.</p>')
  text=replace(text,"<h2>Upominki z herbatką na Chrzciny</h2>",
   '<h2>Upominki z herbatką na Chrzciny</h2>\r\n<p>Herbatka dla gości na Chrzest to niewielki prezent w naturalnym opakowaniu z personalizowanym bilecikiem. Zobacz <a href="https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest">herbatki na Chrzciny</a> oraz dostępne wzory.</p>')
  text=replace(text,"<h2>Świeczki podziękowania na Chrzest</h2>",
   '<h2>Świeczki podziękowania na Chrzest</h2>\r\n<p>Jeśli szukasz upominku o symbolicznym charakterze, sprawdź <a href="https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest">świeczki na Chrzest dla gości</a> z białą świeczką i bilecikiem z imieniem dziecka, datą i własnym tekstem.</p>')
  text=replace(text,"<h2>Upominki dla gości na chrzest roczek - szybka realizacja</h2>",
   '<h2>Jak zamówić personalizowane podziękowania na Chrzest?</h2>\r\n'
   '<p>Wybierz świeczki albo herbatki, a następnie wzór graficzny na Chrzest dziewczynki lub chłopca. Podaj imię dziecka, datę Chrztu i tekst na etykietę. Minimalna liczba sztuk wynosi 30. Zawartość i wymiary prezentów sprawdzisz w opisach produktów.</p>\r\n'
   '<h3>Co napisać na podziękowaniu dla gości na Chrzest?</h3>\r\n'
   '<p>Możesz umieścić krótką dedykację, np. „Dziękujemy za wspólne świętowanie mojego Chrztu Świętego”, a pod nią imię dziecka i datę uroczystości. Tekst warto dopasować do rozmiaru etykiety.</p>\r\n'
   '<h3>Ile upominków na Chrzciny zamówić?</h3>\r\n'
   '<p>Zwykle przygotowuje się jeden upominek dla każdego zaproszonego gościa. Policz potwierdzonych uczestników przyjęcia i kilka dodatkowych sztuk, pamiętając o minimum 30 sztuk.</p>\r\n'
   '<h3>Gdzie ułożyć prezenciki dla gości na Chrzest?</h3>\r\n'
   '<p>Personalizowane świeczki i herbatki można rozłożyć przy nakryciach lub wręczyć na zakończenie przyjęcia. Takie podziękowania łączą dekorację stołu z drobną pamiątką.</p>\r\n'
   '<h2>Upominki dla gości na chrzest roczek - szybka realizacja</h2>')
  payload["description"]=text
 elif id==4929:
  payload.update({"name":"Świeczka na Chrzest w opakowaniu EKO – podziękowanie dla gości",
   "metaTitle":"Świeczka na Chrzest z personalizacją | Papiernia",
   "metaDescription":"Świeczka na Chrzest z etykietą i dedykacją – podziękowanie dla gości. Biała świeczka, papier EKO i wzory do wyboru. Personalizacja od 30 sztuk."})
  text=replace(text,'<h3 class="" style="text-align: center;" data-start="0" data-end="44">Świeczki – Upominki na Chrzest dla Gości</h3>',
   '<h2 style="text-align: center;">Świeczka na Chrzest w opakowaniu EKO – podziękowanie dla gości</h2>')
  text=replace(text,'Szukasz wyjątkowego sposobu na podziękowanie gościom za ich obecność na Chrzcie? Świeczki to idealny wybór - prezenciki dla przybyłych gości na przyjęcie z okazji Chrztu Świętego to doskonały pomysł, aby w oryginalny sposób podziękować im za obecność w tak ważnym dniu. Nasza oferta obejmuje szeroką gamę gotowych drobnych upominków, które można dostosować do charakteru Twojej uroczystości.',
   'Świeczka na Chrzest w oprawie z brązowego papieru EKO to drobny, symboliczny prezent dla gości. Biała świeczka i personalizowany bilecik z imieniem dziecka, datą Chrztu Świętego oraz własnym tekstem tworzą gotowe podziękowanie. Upominek można ułożyć przy nakryciu lub wręczyć po przyjęciu.')
  text=replace(text,'<h3 class="" style="text-align: center;" data-start="981" data-end="1020">Personalizowane Upominki na Chrzest</h3>',
   '<h2 style="text-align: center;">Personalizowane świeczki na Chrzciny dla gości</h2>')
  text=replace(text,'Nasza oferta obejmuje szeroką gamę upominków, które można dostosować do charakteru Twojej uroczystości. Dodatkowo, bez dodatkowych kosztów oferujemy możliwość personalizacji – na upomoinkach można umieścić imię dziecka, datę uroczystości i krótkie podziękowanie, co sprawia, że każdy gość poczuje się wyjątkowo otrzymująć unikalne i jedyny w swoim rodzaju upominek.',
   'Personalizacja etykiety jest wliczona w cenę. Podaj imię dziecka, datę Chrztu Świętego i krótki tekst podziękowania. Biała świeczka i brązowy papier EKO pasują do wielu dekoracji, a dostępne modele graficzne pozwalają dobrać motyw na Chrzest dziewczynki lub chłopca.')
  text=replace(text,'<h3 class="" style="text-align: center;" data-start="1664" data-end="1702">Wyjątkowe Podziękowania na Chrzest</h3>',
   '<h2 style="text-align: center;">Świeczki na Chrzest – pamiątka dla gości</h2>')
  text=replace(text,'Zapraszamy do zapoznania sią z naszą ofertą personalizowanych upominków na Chrzest: Ciasteczka z wróżbą, słodkie upominki, kartki z czekoladką, magnesy, herbatki i wiele innych. Więcej propozycji prezentów na Chrcini i roczek, w katetogorii -',
   'Szukasz upominku w innej formie? Zobacz także <a href="https://papiernia.net.pl/herbata-podziekowania-dla-gosci-chrzest">herbatki na Chrzest dla gości</a> lub przejrzyj kategorię ')
  text=replace(text,'"Podziękowania dla gości na Crzest"','"Podziękowania dla gości na Chrzest"')
  payload["fullDescription"]=text
 elif id==4930:
  payload["name"]="Herbatka na Chrzest – personalizowane podziękowanie dla gości"
  text=replace(text,'<h2 style="text-align: center;">Herbatka dla gości na Chrzest – personalizowane podziękowanie</h2>',
   '<h2 style="text-align: center;">Herbatka EKO na Chrzest – podziękowanie dla gości</h2>')
  text=replace(text,'W naszej ofercie znajdziesz również inne personalizowane prezenty przygotowane specjalnie na Chrzest Święty. Są to między innymi ciasteczka z wróżbą, słodkie upominki, kartki z czekoladką, magnesy, herbatki oraz inne drobiazgi, które możesz dopasować do charakteru przyjęcia.',
   'W kategorii Chrzest oferujemy personalizowane herbatki oraz <a href="https://papiernia.net.pl/podziekowanie-za-przybycie-na-chrzest">świeczki na Chrzest dla gości</a>. Oba rodzaje podziękowań można dopasować do uroczystości i ozdobić etykietą z imieniem dziecka oraz dedykacją.')
  text=replace(text,'Znajdziesz tam różne propozycje prezentów na Chrzciny dla dziewczynki i chłopca.',
   'Znajdziesz tam dostępne upominki na Chrzciny oraz wzory dla dziewczynki i chłopca.')
  payload["fullDescription"]=text
 else:raise ValueError(id)
 if imgtags(old)!=imgtags(text):raise RuntimeError("Image tags changed for "+str(id))
 preserve_links(old,text)
 if id==19 and len(text)<len(old):raise RuntimeError("Category shortened unexpectedly")
 if len(text)<.8*len(old):raise RuntimeError("Product description shortened unexpectedly")
 return payload,old
def save(rows):
 (out/("preview.json" if MODE=="preview" else "deployment.json")).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
def main():
 all=[];report=[];before=[]
 # Preflight and preview EVERY target BEFORE first production write.
 for id in urls:
  check_url(id);cur=snap(id)
  typ,_=urls[id];key="description" if typ=="Category" else "fullDescription"
  h=expected[id]
  for value,want in zip((field(cur,key),field(cur,"name"),field(cur,"metaTitle"),field(cur,"metaDescription")),h):
   if sha(value)!=want:raise RuntimeError(f"Live state differs from audit for {id}; no write")
  payload,old=change(id,cur)
  preview=api("post",f"/v3/Preview{typ}Seo/{id}",json=payload)
  if preview.get("dryRun") is not True:raise RuntimeError("Preview not dry-run")
  token=preview.get("approvalToken",preview.get("ApprovalToken"))
  if not token:raise RuntimeError("Approval token not received")
  row={"id":id,"url":urls[id][1],"status":"PREVIEW_OK",
    "fields":[k for k in payload if k!="reason"],
    "before":{k:field(cur,k) for k in ("name","metaTitle","metaDescription")},
    "after":{k:payload.get(k,field(cur,k)) for k in ("name","metaTitle","metaDescription")},
    "htmlBytesBefore":len(old),"htmlBytesAfter":len(payload.get(key,old)),
    "htmlShaBefore":sha(old),"htmlShaAfter":sha(payload.get(key,old)),
    "imageTags":len(imgtags(old)),"oldLinks":links(old),"newLinks":links(payload.get(key,old))}
  report.append(row);all.append((id,typ,cur,payload,old,token,row));save(report)
  before.append({"id":id,"originalFields":{k:field(cur,k) for k in ("name","metaTitle","metaDescription",key)}})
  print(json.dumps({"id":id,"status":"PREVIEW_OK","fields":row["fields"],"images":row["imageTags"],"linksBefore":len(row["oldLinks"]),"linksAfter":len(row["newLinks"]),"htmlBefore":row["htmlBytesBefore"],"htmlAfter":row["htmlBytesAfter"]},ensure_ascii=False))
 (out/"before-snapshot.json").write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding="utf-8")
 if MODE=="preview":return
 for id,typ,cur,payload,old,token,row in all:
  row["status"]="COMMIT_ATTEMPTED";save(report)
  api("put",f"/v3/Commit{typ}Seo/{id}",json={**payload,"approvalToken":token})
  new=snap(id);key="description" if typ=="Category" else "fullDescription"
  for k,v in payload.items():
   if k=="reason":continue
   if field(new,k)!=v:raise RuntimeError(f"Readback mismatch: {id}/{k}")
  if imgtags(field(new,key) or "")!=imgtags(old):raise RuntimeError("Images changed after commit")
  preserve_links(old,field(new,key) or "")
  for k in ("sku","metaKeywords","shortDescription","published","deleted"):
   if field(new,k)!=field(cur,k):raise RuntimeError(f"Protected field changed: {id}/{k}")
  check_url(id)
  row["status"]="APPLIED_VERIFIED";save(report)
  print(json.dumps({"id":id,"status":"APPLIED_VERIFIED","imageTagsPreserved":len(imgtags(old)),"newLinks":len(links(field(new,key) or ""))},ensure_ascii=False))
if __name__=="__main__":
 try:main()
 except Exception as exc:
  (out/"error.txt").write_text(str(exc)[:500],encoding="utf-8")
  raise
