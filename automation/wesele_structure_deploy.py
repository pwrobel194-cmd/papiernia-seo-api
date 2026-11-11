import os,json,re,html,hashlib,pathlib,requests
from datetime import datetime,timezone

BASE="https://papiernia.net.pl"
API=BASE+"/papiernia-seo-api/v3"
S=requests.Session()
S.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"]})
MODE=os.environ.get("SEO_ACTION","preview").lower()
assert MODE in {"preview","apply"}
WORK=pathlib.Path("reports/wesele-structure")
WORK.mkdir(parents=True,exist_ok=True)
DATA=json.loads((WORK/"snapshot.json").read_text(encoding="utf-8"))
CAT=DATA["categories"];PROD=DATA["products"]
REASON="Zgoda właściciela 11.11.2026: architektura SEO Wesele, rozróżnienie intencji kategorii, linkowanie wewnętrzne, metadane zdjęć; bez zmiany URL, cen, galerii, przypisań produktów"
MARKER="data-papiernia-wesele-seo=\"2026-11-11\""
def call(method,path,payload=None):
 r=S.request(method,API+path,json=payload,timeout=55)
 if not r.ok:raise RuntimeError(f"{method} {path}: HTTP {r.status_code}: {r.text[:550]}")
 j=r.json()
 if j.get("ok") is False:raise RuntimeError(f"{path}: {str(j)[:350]}")
 return j
def sources(s):
 ret=[]
 for t in re.findall(r"<img\b[^>]*>",s or "",re.I|re.S):
  z=re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']',t,re.I)
  ret.append(z.group(1) if z else "")
 return ret
def digest(t):return hashlib.sha256((t or "").encode("utf-8")).hexdigest()
def link(slug,text):
 return '<a href="/'+html.escape(slug,quote=True)+'" title="'+html.escape(text,quote=True)+'">'+html.escape(text)+'</a>'
def ptext(s):return '<p>'+s+'</p>'

MAIN=[
("candles","Świeczki weselne"),("cookies","Ciasteczka z wróżbą na wesele"),
("chocolates","Czekoladki dla gości"),("magnets","Magnesy ślubne"),
("sweets","Słodkie podziękowania"),("scratch","Zdrapki weselne"),
("tea","Herbatki dla gości")
]
THEME=[("funny","Śmieszne podziękowania"),("placecards","Winietki z podziękowaniem")]

def card(label,text):
 slug=CAT[label]["slug"]
 return ('<a href="/'+html.escape(slug)+'" style="box-sizing:border-box;flex:1 1 190px;min-width:185px;'
 'padding:12px 14px;border:1px solid #ddd;border-radius:8px;text-decoration:none;display:block;'
 'background-color:#fafafa;color:#2b2b2b;font-weight:600;" title="'+html.escape(text)+'">'+html.escape(text)+'</a>')
def category_menu():
 parts=['<section '+MARKER+' style="width:100%;max-width:none;box-sizing:border-box;line-height:1.65;margin:18px 0 30px;">',
 '<h2>Wybierz podziękowania dla gości weselnych według rodzaju upominku</h2>',
 '<p>Znajdziesz tu personalizowane prezenty i upominki na wesele w różnych wariantach. Porównaj rodzaj produktu, a następnie wybierz opakowanie i wzór graficzny.</p>',
 '<div style="display:flex;flex-wrap:wrap;gap:10px;width:100%;margin:14px 0 24px;">']
 parts.extend(card(k,t) for k,t in MAIN)
 parts.append('</div><h2>Podziękowania weselne według pomysłu i zastosowania</h2>')
 parts.append('<p>Jeżeli szukasz upominków z zabawnymi tekstami albo prezentów, które równocześnie pełnią funkcję winietki, wybierz jedną z poniższych kolekcji. Ten sam produkt może należeć do kilku kolekcji, ale jego karta zakupu pozostaje jedna.</p>')
 parts.append('<div style="display:flex;flex-wrap:wrap;gap:10px;width:100%;margin:14px 0 24px;">')
 parts.extend(card(k,t) for k,t in THEME)
 parts.append('</div><h2>Jak wybrać upominek na wesele?</h2>')
 parts.append('<p><strong>Słodkie upominki:</strong> ciasteczka z wróżbą, czekoladki i cukierki to małe podziękowania dla gości na stół. <strong>Trwała pamiątka:</strong> magnesy mogą zostać z gośćmi na lata, a mini świeczki są praktycznym, dekoracyjnym prezentem. <strong>Dodatkowa funkcja:</strong> zdrapki i winietki 2w1 łączą drobny gest z zabawą albo organizacją miejsc przy stole.</p>')
 parts.append('<p>W opisach konkretnych produktów sprawdzisz wymiary, możliwości personalizacji, minimalną liczbę sztuk oraz to, czy opakowanie jest dostarczane <strong>do samodzielnego złożenia</strong>. Dzięki temu dobierzesz upominek do liczby gości i stylu przyjęcia.</p></section>')
 return "\n".join(parts)

# Niezależne intencje – żaden z istniejących opisów kategorii nie jest skracany.
SETTINGS={
 "main":{
  "name":"Podziękowania dla gości weselnych – upominki na wesele",
  "metaTitle":"Podziękowania dla gości weselnych – upominki na wesele",
  "metaDescription":"Podziękowania dla gości weselnych i personalizowane upominki na wesele: ciasteczka, świeczki, czekoladki, magnesy, winietki i inne prezenciki.",
  "alt":"Podziękowania dla gości weselnych – upominki ślubne z personalizacją"},
 "candles":{
  "name":"Świeczki dla gości weselnych – podziękowania na ślub",
  "metaTitle":"Świeczki na wesele – podziękowania dla gości | Papiernia",
  "metaDescription":"Personalizowane świeczki dla gości weselnych w pudełkach i ozdobnym papierze. Drobne podziękowania na ślub ze świeczką i etykietą.",
  "alt":"Świeczki na wesele – personalizowane podziękowania dla gości",
  "title":"Mini świeczki i podziękowania dla gości weselnych",
  "intro":"Mini świeczki na podziękowania weselne można podarować w białym pudełeczku, pudełku EKO lub papierowym opakowaniu. Każdy wariant ma własne wymiary, etykietę i sposób przygotowania. Wybierz zestaw odpowiadający aranżacji stołów.",
  "product_ids":[4885,4886,4902],
  "extra":"Porównaj opakowania i sprawdź na karcie produktu, czy etykietę trzeba nakleić, a pudełeczko samodzielnie złożyć."},
 "chocolates":{
  "name":"Czekoladki na wesele – podziękowania dla gości",
  "metaTitle":"Czekoladki na wesele dla gości z nadrukiem | Papiernia",
  "metaDescription":"Personalizowane czekoladki na wesele: kartki z czekoladką, mini czekoladki z etykietą i upominki ślubne z nadrukiem. Zobacz warianty.",
  "alt":"Czekoladki na wesele – personalizowane podziękowania dla gości",
  "title":"Czekoladki ślubne dla gości – dostępne warianty",
  "intro":"Czekoladki na wesele występują w kilku formach: jako kartka z podziękowaniem i czekoladką lub mini czekoladka z personalizowaną etykietą. Ta kategoria służy przede wszystkim porównaniu wariantów z czekoladą, a pozostałe rodzaje słodyczy znajdziesz w szerszej kolekcji.",
  "product_ids":[4905,4887,4890],
  "extra":"Sprawdź formę opakowania oraz możliwości dodania imion Pary Młodej, daty ślubu i krótkich życzeń."},
 "magnets":{
  "name":"Magnesy na wesele – podziękowania dla gości",
  "metaTitle":"Magnesy na wesele dla gości – z personalizacją | Papiernia",
  "metaDescription":"Magnesy na wesele jako personalizowane podziękowania dla gości. Wybierz wzory kwiatowe lub grafiki z humorem i dodaj imiona oraz datę ślubu.",
  "alt":"Personalizowane magnesy ślubne – upominki dla gości na wesele",
  "title":"Wybierz magnesy jako podziękowania na wesele",
  "intro":"Magnesy ślubne dla gości to trwała pamiątka uroczystości. Wybierz wzory kwiatowe lub bardziej żartobliwą grafikę – wszystkie odwołują się do jednej, konkretnej formy produktu, czyli magnesu.",
  "product_ids":[4889,4901],
  "extra":"Jeżeli zależy Ci głównie na zabawnym tekście, sprawdź także kolekcję podziękowań z humorem."},
 "sweets":{
  "metaTitle":"Słodkie podziękowania dla gości na wesele | Papiernia",
  "metaDescription":"Słodkie podziękowania na wesele: personalizowane cukierki i czekoladki dla gości. Poznaj również ciasteczka z wróżbą w osobnej kolekcji.",
  "alt":"Słodkie podziękowania dla gości weselnych – cukierki i czekoladki",
  "title":"Słodkie upominki weselne – wybierz rodzaj słodyczy",
  "intro":"W tej kolekcji znajdziesz słodycze na podziękowanie dla gości: cukierki oraz różne wersje mini czekoladek i kartek z czekoladką. Jeżeli szukasz konkretnego rodzaju słodyczy, przejdź bezpośrednio do odpowiedniego produktu lub do kategorii czekoladek.",
  "product_ids":[4891,4905,4887,4890],
  "extra":"Osobno dostępne są także ciasteczka z wróżbą na wesele, w pudełeczkach, torebkach i z winietką 2w1."},
 "funny":{
  # Nie zmieniamy nazwy ani meta – kategoria dobrze pozycjonowana.
  "alt":"Śmieszne podziękowania dla gości weselnych – upominki z humorem",
  "title":"Śmieszne podziękowania – produkty i wzory z humorem",
  "intro":"Ta kolekcja grupuje różne typy produktów według ich humorystycznej oprawy graficznej i tekstów: ciasteczka z wróżbą, czekoladki, cukierki i magnesy. Nie jest osobnym rodzajem produktu, dlatego warianty te znajdziesz też w ich podkategoriach produktowych.",
  "product_ids":[4884,4905,4891,4889],
  "extra":"Jeśli bardziej zależy Ci na rodzaju upominku niż na zabawnym wzorze, wybierz kategorię ciasteczek, czekoladek lub magnesów."},
 "scratch":{
  # Chronimy już zdobyte pozycje, nie zmieniamy H1 i title.
  "alt":"Zdrapki weselne jako podziękowania dla gości i zadania na wesele",
  "title":"Zdrapki weselne – prezent i zabawa na przyjęciu",
  "intro":"Zdrapki dla gości weselnych mogą być pamiątką z podziękowaniem lub elementem wspólnej zabawy z zadaniami. Sprawdź dokładną formę produktu i możliwość personalizacji, zanim zamówisz nakład na uroczystość.",
  "product_ids":[4895],
  "extra":"Dla osób szukających podziękowania łączącego kilka funkcji przygotowaliśmy także kategorię winietek."},
 "placecards":{
  # H1 oraz meta zostają – osobna mocna intencja 2w1.
  "alt":"Winietki z podziękowaniem dla gości weselnych – prezenciki 2w1",
  "title":"Winietki i podziękowanie dla gości w jednym",
  "intro":"Winietka z podziękowaniem 2w1 łączy oznaczenie miejsca przy stole z drobnym upominkiem. Na tej stronie pokazujemy rozwiązanie z ciasteczkiem z wróżbą i imienną winietką – produkt dostępny jest również w kategorii ciasteczek weselnych.",
  "product_ids":[4904],
  "extra":"Przygotuj listę gości zgodnie z miejscami przy stole, a na etykietach możesz umieścić własny tekst podziękowania."},
 "tea":{
  "name":"Herbatki na wesele – podziękowania dla gości",
  "metaTitle":"Herbatki na wesele – podziękowania dla gości | Papiernia",
  "metaDescription":"Personalizowana herbatka na wesele jako upominek i podziękowanie dla gości. Ozdobna etykieta z imionami, datą ślubu i wybranym wzorem.",
  "alt":"Herbatka dla gości weselnych – personalizowane podziękowanie",
  "title":"Herbatka dla gości na wesele – personalizowany upominek",
  "intro":"Herbatka z personalizowaną etykietą to propozycja dla par, które wolą nieduży, aromatyczny upominek zamiast słodyczy lub świeczki. Zobacz dostępny zestaw i sprawdź informacje o składzie i przygotowaniu zamówienia.",
  "product_ids":[4892],
  "extra":"Herbatka może stanowić samodzielne podziękowanie albo uzupełnienie prezentu dla gości."}
}
PRODUCT_ANCHORS={
4885:("candles","świeczek weselnych"),
4886:("candles","mini świeczek weselnych"),
4902:("candles","świeczek dla gości weselnych"),
4892:("tea","herbatek na podziękowania weselne"),
4905:("chocolates","czekoladek na wesele"),
4887:("chocolates","czekoladek dla gości weselnych"),
4890:("chocolates","czekoladek na wesele z personalizacją"),
4891:("sweets","słodkich podziękowań weselnych"),
4895:("scratch","zdrapek na wesele"),
4889:("magnets","magnesów na wesele"),
4901:("magnets","personalizowanych magnesów weselnych"),
4906:("main","upominków i podziękowań dla gości weselnych")
}
ID_NAMES={v["id"]:v["snapshot"]["name"] for v in PROD.values()}
ID_SLUGS={v["id"]:slug for slug,v in PROD.items()}
def category_extra(key):
 p=SETTINGS[key]
 if key=="main":
  return category_menu()
 parts=['<section '+MARKER+' style="width:100%;max-width:none;box-sizing:border-box;line-height:1.7;margin:28px 0;">',
 '<h2>'+html.escape(p["title"])+'</h2>',ptext(html.escape(p["intro"])),
 '<h3>Sprawdź dostępne warianty</h3><ul>']
 for eid in p["product_ids"]:
  parts.append('<li>'+link(ID_SLUGS[eid],ID_NAMES[eid])+'</li>')
 parts.append('</ul>'+ptext(html.escape(p["extra"])))
 if key=="sweets":
  parts.append(ptext('Wybierz także '+link(CAT["cookies"]["slug"],"ciasteczka z wróżbą na wesele")+' – osobną kategorię upominków z losową wróżbą.'))
 if key=="funny":
  parts.append(ptext('Porównaj również '+link(CAT["cookies"]["slug"],"ciasteczka weselne z wróżbą")+', '+link(CAT["chocolates"]["slug"],"czekoladki na wesele")+' oraz '+link(CAT["magnets"]["slug"],"magnesy ślubne")+'.'))
 if key=="placecards":
  parts.append(ptext('Pełną ofertę zestawów zawierających ciasteczko znajdziesz w kategorii '+link(CAT["cookies"]["slug"],"ciasteczka z wróżbą dla gości weselnych")+'.'))
 if key=="candles":
  parts.append(ptext('Dla porównania innych rodzajów podziękowań wróć do kategorii '+link(CAT["main"]["slug"],"upominki na wesele")+'.'))
 elif key not in {"funny","placecards"}:
  parts.append(ptext('Zobacz również '+link(CAT["main"]["slug"],"wszystkie podziękowania dla gości weselnych")+'.'))
 else:
  parts.append(ptext('Wróć do kategorii '+link(CAT["main"]["slug"],"podziękowania dla gości weselnych")+'.'))
 parts.append('</section>')
 return "\n".join(parts)
REPORT={"timestamp":datetime.now(timezone.utc).isoformat(),"mode":MODE,"categoryChanges":[],"productChanges":[],"pictureChanges":[],"errors":[]}
TASKS=[]
for key,p in SETTINGS.items():
 c=CAT[key];cur=c["snapshot"]
 if not cur.get("Published") or cur.get("Deleted"):raise RuntimeError("Inactive category: "+key)
 if not c.get("canonical","").endswith("/"+c["slug"]):raise RuntimeError("Unexpected canonical "+key)
 old=cur.get("Description") or ""
 if MARKER in old: new=old
 else: new=(category_extra(key)+"\n"+old) if key=="main" else (old+"\n"+category_extra(key))
 if len(new)<len(old):raise RuntimeError("Category description truncated")
 if sources(old)!=sources(new):raise RuntimeError("Category images moved "+key)
 payload={"description":new}
 for field in ("name","metaTitle","metaDescription"):
  if p.get(field) is not None:
   old_key={"name":"name","metaTitle":"MetaTitle","metaDescription":"MetaDescription"}[field]
   if cur.get(old_key)!=p[field]:payload[field]=p[field]
 if new==old:payload.pop("description")
 if payload:TASKS.append(("Category",cur["id"],payload,key,cur))
for slug,v in PROD.items():
 x=v["snapshot"];eid=x["id"]
 if not x["Published"] or x["Deleted"]:continue
 if eid not in PRODUCT_ANCHORS:continue
 key,anchor=PRODUCT_ANCHORS[eid]
 assert CAT[key]["id"] in x["categoryIds"], f"Product {eid} not in {key}"
 old=x.get("FullDescription") or ""
 dest=CAT[key]["slug"]
 if dest in old or MARKER in old:continue
 addition='<p '+MARKER+' style="margin:20px 0;line-height:1.7;">Zobacz także inne warianty '+link(dest,anchor)+' w Papierni.</p>'
 new=old+"\n"+addition
 if sources(old)!=sources(new):raise RuntimeError("Product images moved "+str(eid))
 TASKS.append(("Product",eid,{"fullDescription":new},slug,x))
print("PLAN","categories",sum(t[0]=="Category" for t in TASKS),"products",sum(t[0]=="Product" for t in TASKS),flush=True)
( WORK/"before-state.json").write_text(json.dumps({"categories":CAT,"products":PROD},ensure_ascii=False,indent=2),encoding="utf-8")
def log():
 (WORK/"deployment-report.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding="utf-8")
def preserve_after(kind,id,old,current,changes):
 if current["slug"]!=old["slug"]:raise RuntimeError("Slug changed "+str(id))
 if kind=="Product":
  if [p["Id"] for p in current["pictures"]] !=[p["Id"] for p in old["pictures"]]:raise RuntimeError("Gallery changed "+str(id))
  if current["categoryIds"]!=old["categoryIds"]:raise RuntimeError("Assignments changed "+str(id))
  if sources(current["FullDescription"])!=sources(old["FullDescription"]):raise RuntimeError("Images changed "+str(id))
 else:
  if sources(current["Description"])!=sources(old["Description"]):raise RuntimeError("Category images changed "+str(id))
for kind,eid,payload,key,orig in TASKS:
 try:
  preview=call("POST",f"/Preview{kind}Seo/{eid}",payload)
  if not preview.get("dryRun") or not preview.get("approvalToken"):raise RuntimeError("Missing API signed token")
  if MODE=="apply":
   outcome=call("PUT",f"/Commit{kind}Seo/{eid}",{**payload,"approvalToken":preview["approvalToken"],"reason":REASON})
   if not outcome.get("committed"):raise RuntimeError("Commit not confirmed")
   after=call("GET",f"/{kind}Snapshot/{eid}")
   for field,val in payload.items():
    k={"name":"name","description":"Description","fullDescription":"FullDescription","metaTitle":"MetaTitle","metaDescription":"MetaDescription"}[field]
    if after.get(k)!=val:raise RuntimeError("Read-back mismatch "+field)
   preserve_after(kind,eid,orig,after,payload)
  entry={"id":eid,"slug":orig["slug"],"fields":list(payload),"verification":"committed_and_verified" if MODE=="apply" else "preview_ok","before_hash":digest(orig.get("FullDescription") if kind=="Product" else orig.get("Description")),"after_hash":digest(payload.get("fullDescription") or payload.get("description") or "")}
  REPORT["categoryChanges" if kind=="Category" else "productChanges"].append(entry)
  print("RESULT",kind,key,eid,entry["verification"],",".join(payload),flush=True);log()
 except Exception as e:
  REPORT["errors"].append({"kind":kind,"id":eid,"key":key,"error":str(e)});log();raise

# Główne zdjęcia kategorii: bez edycji plików i kolejności obrazów.
for key,p in SETTINGS.items():
 c=CAT[key]["snapshot"];eid=c["id"];pic=c.get("picture")
 if not pic or pic["Id"]<=0:continue
 alt=p["alt"];title=(p.get("name") or c["name"])+" | Papiernia"
 if pic.get("AltAttribute")==alt and pic.get("TitleAttribute")==title:continue
 scope={"scope":"category","pictureId":pic["Id"],"altAttribute":alt,"titleAttribute":title}
 try:
  preview=call("POST",f"/PreviewPictureMetadata/{eid}",scope)
  if not preview.get("dryRun") or not preview.get("approvalToken"):raise RuntimeError("Picture preview invalid")
  if MODE=="apply":
   result=call("PUT",f"/CommitPictureMetadata/{eid}",{**scope,"approvalToken":preview["approvalToken"],"reason":REASON})
   if not result.get("committed"):raise RuntimeError("Picture commit not confirmed")
   after=call("GET",f"/CategorySnapshot/{eid}")
   if after["picture"]["Id"]!=pic["Id"] or after["picture"]["AltAttribute"]!=alt or after["picture"]["TitleAttribute"]!=title:
    raise RuntimeError("Picture readback mismatch")
  entry={"id":eid,"pictureId":pic["Id"],"key":key,"before":{"alt":pic.get("AltAttribute"),"title":pic.get("TitleAttribute")},"after":{"alt":alt,"title":title},"verification":"committed_and_verified" if MODE=="apply" else "preview_ok"}
  REPORT["pictureChanges"].append(entry)
  print("PICTURE",key,pic["Id"],entry["verification"],flush=True);log()
 except Exception as e:
  REPORT["errors"].append({"picture":key,"error":str(e)});log();raise
print("COMPLETE",MODE,"categories",len(REPORT["categoryChanges"]),"products",len(REPORT["productChanges"]),"pictures",len(REPORT["pictureChanges"]),"errors",len(REPORT["errors"]),flush=True)
