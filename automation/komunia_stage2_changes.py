"""Guarded Komunia SEO stage 2, existing Papiernia SEO API v3.
Default: PREVIEW ONLY. For reviewed explicit deployment set SEO_MODE=apply.
No changes to URL, picture media, galleries, prices, categories or publication.
"""
import hashlib,json,os,pathlib,re,requests,sys
BASE="https://papiernia.net.pl/papiernia-seo-api/v3"
MODE=os.environ.get("SEO_MODE","preview").lower()
if MODE not in ("preview","apply"): raise RuntimeError("Unsupported mode")
S=requests.Session()
S.headers.update({"X-Papiernia-SEO-Key":os.environ["PAPIERNIA_SEO_API_KEY"],"Accept":"application/json"})
DEST=pathlib.Path("audit/komunia-20261108-stage2")
DEST.mkdir(parents=True,exist_ok=True)
EXPECTED={
 4907:{"full":"c875517210a0313d26e87510cf147e527c7334b526309ce46f55606919a9a189",
       "name":"5fe40fba256262461901951f093a914f644bf5ff85277e60390508fc378d16ce",
       "title":"2b331461aca7b61994494bedfa933655e5e8bf51520f4e4871d027d4fe654b0a",
       "desc":"9ab98f7436071f1284239859f01f2c16c0b9cb5d4acb31f0d0c6e4e0a08440b7",
       "short":"aef26cfce0ec20d94800086f4951bf658cb5bd239e2b48204eef1771bdb141dd"},
 4893:{"full":"32c6ea080291a72a837bd2ec92d4a707256618dd0538237fe7544d8a9f02b562",
       "name":"9fdf13e39d816f769b12565609de04d123789958fbcc3be71a193d818726fc3d",
       "title":"c37f04f6d254efa9edfb1a16808a47d261b0cc1869932483df95561e58683b7c",
       "desc":"4cb34ca19c5a58c32834d1ad54bb32dc111353bb08cfcabf987b4a05f4e49142",
       "short":"0764d865960397bd6ca6babb1372337e0912c20f46566fdda81b0067a4226f16"},
 4909:{"full":"b7c6be034c3dbda16d1e43fb2b24db0e96c7128c51270320485020142b79be23",
       "name":"71d00602fe5027e4091a8e3a04c62e31b067f243bc188b6e7561b8167a2e311a",
       "title":"d74e562a11d880d223fcc72445a91a04bf17b57d9fda3e06f9463c6878fdf818",
       "desc":"de8352d3f1176d4e324f1eeaeeb94ee2463619a3a39cafa33e7052bb09bbdd95",
       "short":"deb2d5e985ff278a30d85e8e0383c72401cbeaaee0356dee0f960f26dd91150a"}
}
def sha(x):return hashlib.sha256((x or "").encode("utf-8")).hexdigest()
def field(x,k):return x.get(k,x.get(k[0].upper()+k[1:]))
def snapshot(id):
 r=S.get(f"{BASE}/ProductSnapshot/{id}",timeout=40);r.raise_for_status()
 o=r.json();return o.get("data",o.get("snapshot",o))
def call(method,path,payload):
 r=getattr(S,method)(f"{BASE}/{path}",json=payload,timeout=55)
 r.raise_for_status()
 x=r.json()
 if x.get("ok") is False or x.get("success") is False:raise RuntimeError(f"API negative: {path}")
 return x
def once(s,old,new):
 n=s.count(old)
 if n!=1:raise RuntimeError(f"Exact match count {n} (expected 1) for {old[:100]!r}")
 return s.replace(old,new,1)
def paragraph_after(s,heading,index,text):
 at=s.find(heading)
 if at<0:raise RuntimeError("Heading not found")
 remaining=s[at+len(heading):]
 ps=list(re.finditer(r"<p\b[^>]*>(.*?)</p>",remaining,re.I|re.S))
 if len(ps)<=index:raise RuntimeError("Paragraph not found")
 m=ps[index]; before=remaining[:m.start(1)];old=m.group(1)
 if re.search(r"<(?:img|a)\b",old,re.I):raise RuntimeError("Refusing to overwrite paragraph with media/link")
 # Never replace a paragraph after a later unrelated section; require relatively close.
 if m.start()>1500:raise RuntimeError("Paragraph too far after target heading")
 new_rem=remaining[:m.start(1)]+text+remaining[m.end(1):]
 return s[:at+len(heading)]+new_rem
def anchor_hrefs(s):
 return re.findall(r"<a\b[^>]*\bhref=[\"']([^\"']+)[\"']",s,re.I)
URLS={4907:"https://papiernia.net.pl/czekoladki-komunijne-slodkie-podziekowanie",
      4893:"https://papiernia.net.pl/czekoladki-na-komunie-upominki-dla-gosci",
      4909:"https://papiernia.net.pl/ciasteczka-z-wrozba-dla-gosci-na-komunie"}
def verify_public_url(id):
 url=URLS[id]
 root=BASE.rsplit("/v3",1)[0]
 response=S.get(root+"/v1/Resolve",params={"url":url},timeout=35)
 response.raise_for_status()
 result=response.json()
 actual=field(result,"id")
 if str(actual)!=str(id) or str(field(result,"entity")).lower()!="product":
  raise RuntimeError(f"Public URL mapping changed for {id}")

def prepare(id,cur):
 e=EXPECTED[id]
 for k,api in (("full","fullDescription"),("name","name"),("title","metaTitle"),("desc","metaDescription"),("short","shortDescription")):
  if sha(field(cur,api))!=e[k]:raise RuntimeError(f"Before-state changed: {id} / {k}")
 old=field(cur,"fullDescription") or "";html=old;payload={}
 oldshort=field(cur,"shortDescription") or ""
 if id==4907:
  payload.update({
   "name":"Kartka z czekoladką na Komunię – podziękowanie dla gości",
   "metaTitle":"Kartka z czekoladką na Komunię dla gości | Papiernia",
   "metaDescription":"Kartka A6 z czekoladką na Pierwszą Komunię Świętą. Personalizowane podziękowania dla gości i wzory do wyboru. Zestaw do samodzielnego zapakowania."})
  oh='<h2 style="text-align: center;">Upominki Komunijne - słodkie podziękowania dla gości&nbsp;</h2>'
  nh='<h2 style="text-align: center;">Kartka z czekoladką na Komunię – podziękowanie dla gości</h2>'
  html=once(html,oh,nh)
  html=paragraph_after(html,nh,0,
   "Kartka A6 z czekoladką Chocolate Hills i własną dedykacją to słodkie podziękowanie dla gości na Pierwszą Komunię Świętą. Na ozdobnej kartce umieścimy imię dziecka, datę uroczystości i krótki tekst podziękowania. Zestaw zawiera przezroczystą folijkę z taśmą do samodzielnego zapakowania.")
  html=paragraph_after(html,nh,1,
   "Taką kartkę z czekoladką można położyć przy nakryciu każdego gościa lub wręczyć po zakończeniu przyjęcia komunijnego. To personalizowany upominek na Komunię, który łączy życzenia z niewielką słodkością.")
  h3old='<h3 style="text-align: center;">Spersonalizowane Upominki na Komunię</h3>'
  h3new='<h3 style="text-align: center;">Personalizowane kartki z czekoladką na Pierwszą Komunię Świętą</h3>'
  html=once(html,h3old,h3new)
  html=paragraph_after(html,h3new,0,
   "Motyw graficzny kartki i podziękowanie dopasujemy do imienia dziecka, daty Pierwszej Komunii Świętej oraz wybranego wzoru. Kartka i czekoladka są dostarczane jako zestaw z folijką celofanową do samodzielnego zapakowania.")
  html=once(html,'Wykonane z najwyższej jakości mlecznej czekolady',
    'Ozdobna kartka A6, czekoladka Chocolate Hills oraz folijka z taśmą do samodzielnego zapakowania')
  payload["shortDescription"]=once(oldshort,
   "<b> Gotowe personalizowane upominki dla Gości na Komunię</b>",
   "<b>Kartka A6 z czekoladką na Komunię – personalizowane podziękowanie dla gości (zestaw do samodzielnego zapakowania)</b>")
  html=once(html,'<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą',
   '<p style="text-align: center;">Wolisz czekoladkę w papierowej owijce? Zobacz także <a href="https://papiernia.net.pl/czekoladki-na-komunie-upominki-dla-gosci">czekoladki na Komunię z personalizowaną etykietą</a>.</p>\r\n<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą')
 if id==4893:
  payload.update({
   "metaTitle":"Czekoladki na Komunię z etykietą dla gości | Papiernia",
   "metaDescription":"Czekoladki na Komunię w białej lub eko owijce z personalizowaną etykietą. Słodkie podziękowania dla gości komunijnych, wzory do wyboru. Od 30 sztuk."})
  h2old='<h2 style="text-align: center;">Czekoladki komunijne dla gości - gotowa forma podziękowania&nbsp;</h2>'
  h2new='<h2 style="text-align: center;">Czekoladki na Komunię z etykietą – podziękowanie dla gości</h2>'
  html=once(html,h2old,h2new)
  html=paragraph_after(html,h2new,0,
   "Czekoladki w papierowej owijce z personalizowaną etykietą to słodkie podziękowania dla gości na Pierwszą Komunię Świętą. Do wyboru są białe lub mleczne czekoladki Chocolate Hills oraz biały albo brązowy papier. Na etykiecie umieścimy imię dziecka, datę uroczystości i krótki tekst. Etykietę samoprzylepną dołączamy do samodzielnego naklejenia.")
  h3old='<h3 style="text-align: center;">Gotowy personalizowany upominek&nbsp;</h3>'
  h3new='<h3 style="text-align: center;">Czekoladki komunijne – wybierz papier, wzór i tekst</h3>'
  html=once(html,h3old,h3new)
  html=paragraph_after(html,h3new,0,
   "Wybierz czekoladkę białą lub mleczną, papier biały albo brązowy (eko) i komunijny motyw graficzny. Podaj dane do personalizacji przy zamówieniu. Samoprzylepną etykietę 45 × 45 mm otrzymasz do samodzielnego naklejenia na papierowe opakowanie.")
  html=once(html,"Więcej propozycji prezentów weselnych","Więcej propozycji prezentów komunijnych")
  html=once(html,'title="Podziękowania dla gości wesele"','title="Podziękowania dla gości na Komunię"')
  html=once(html,'<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą',
   '<p style="text-align: center;">Szukasz upominku w innej formie? Sprawdź <a href="https://papiernia.net.pl/czekoladki-komunijne-slodkie-podziekowanie">kartki A6 z czekoladką na Komunię</a> i <a href="https://papiernia.net.pl/magnesy-komunijne-dla-gosci">personalizowane magnesy dla gości komunijnych</a>.</p>\r\n<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą')
 if id==4909:
  payload.update({
   "metaTitle":"Ciasteczka z wróżbą na Komunię dla gości | Papiernia",
   "metaDescription":"Ciasteczka z wróżbą na Pierwszą Komunię Świętą z personalizowanym bilecikiem. Oryginalne podziękowania dla gości i wzory komunijne do wyboru. Od 30 sztuk."})
  h2old='<h2 style="text-align: center;"><strong>Ciasteczko z wróżbą dla gości Komunijnych - upominek spersonalizowany&nbsp;</strong></h2>'
  h2new='<h2 style="text-align: center;"><strong>Ciasteczka z wróżbą na Komunię – podziękowania dla gości</strong></h2>'
  html=once(html,h2old,h2new)
  html=paragraph_after(html,h2new,0,
   "Ciasteczka z wróżbą z personalizowanym bilecikiem to oryginalne podziękowanie dla gości na Pierwszą Komunię Świętą. Można je ułożyć przy nakryciach lub wręczyć na zakończenie przyjęcia komunijnego. Złoty bilecik i etykieta z imieniem dziecka, datą uroczystości i krótkim podziękowaniem nadają temu drobnemu upominkowi wyjątkowy charakter.")
  html=once(html,'<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą',
   '<p style="text-align: center;">Jeśli wolisz trwałą pamiątkę, zobacz również <a href="https://papiernia.net.pl/magnesy-komunijne-dla-gosci">magnesy komunijne dla gości</a>.</p>\r\n<p style="text-align: center;">Zapraszamy do zapoznania sią z naszą')
 if html==old:raise RuntimeError("Unexpected unchanged HTML")
 payload["fullDescription"]=html
 payload["reason"]="SEO Komunia stage 2: distinct occasion/product intent, corrections, guarded internal links"
 if not any("komuni" in str(x).lower() for x in payload.values()):raise RuntimeError("Occasion missing")
 # Existing pictures absolutely unchanged (src, alt, title, order, attrs).
 imgpat=r"<img\b[^>]*>"
 if re.findall(imgpat,old,re.I)!=re.findall(imgpat,html,re.I):raise RuntimeError(f"HTML images changed {id}")
 # Pre-existing anchor hrefs in same order and unchanged, new internal links may be inserted.
 original=anchor_hrefs(old);updated=anchor_hrefs(html);cursor=iter(updated)
 if not all(any(x==wanted for x in cursor) for wanted in original):raise RuntimeError("Old links altered or reordered")
 verify_public_url(id) # public URL maps to target despite v3 snapshot omitting seName
 return payload,old,original

def main():
 targets=[]
 # Validate ALL target states and previews before any write.
 for id in (4907,4893,4909):
  current=snapshot(id)
  payload,old,oldlinks=prepare(id,current)
  preview=call("post",f"PreviewProductSeo/{id}",payload)
  if preview.get("dryRun") is not True:raise RuntimeError("Preview not in dry run")
  token=preview.get("approvalToken",preview.get("ApprovalToken"))
  if not token:raise RuntimeError("Missing approval token")
  targets.append((id,current,payload,old,oldlinks,token))
  print(json.dumps({"id":id,"mode":MODE,"state":"PREVIEW_OK","fields":[k for k in payload if k!="reason"],
    "oldImages":len(re.findall(r'<img\b[^>]*>',old,re.I)),
    "oldLinks":len(oldlinks),"newLinks":len(anchor_hrefs(payload["fullDescription"]))},ensure_ascii=False))
 report=[]
 if MODE=="preview":
  for id,current,payload,old,oldlinks,token in targets:
   report.append({"id":id,"status":"PREVIEW_OK",
     "before":{k:field(current,k) for k in ("name","metaTitle","metaDescription")},
     "after":{k:payload.get(k,field(current,k)) for k in ("name","metaTitle","metaDescription")},
     "fieldsChanged":[k for k in payload if k!="reason"],"oldHtmlSha":sha(old),
     "newHtmlSha":sha(payload["fullDescription"]),
     "imagesUnchanged":len(re.findall(r"<img\b[^>]*>",old,re.I)),
     "oldLinkTargets":oldlinks,"newLinkTargets":anchor_hrefs(payload["fullDescription"])})
  (DEST/"preview-stage2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
  return
 try:
  for id,current,payload,old,oldlinks,token in targets:
   row={"id":id,"status":"COMMIT_ATTEMPTED"}
   report.append(row)
   (DEST/"deployment-stage2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
   call("put",f"CommitProductSeo/{id}",{**payload,"approvalToken":token})
   new=snapshot(id)
   for k,v in payload.items():
    if k=="reason":continue
    if field(new,k)!=v:raise RuntimeError(f"Readback mismatch for {id}, {k}")
   for k in ("seName","metaKeywords","sku","published","deleted"):
    if field(new,k)!=field(current,k):raise RuntimeError(f"Protected field changed: {id}, {k}")
   if "shortDescription" not in payload and field(new,"shortDescription")!=field(current,"shortDescription"):
    raise RuntimeError(f"Short desc changed unexpectedly for {id}")
   verify_public_url(id)
   if re.findall(r"<img\b[^>]*>",old,re.I)!=re.findall(r"<img\b[^>]*>",field(new,"fullDescription") or "",re.I):
    raise RuntimeError("Image tag integrity failed")
   row.update({"status":"APPLIED_VERIFIED",
    "before":{k:field(current,k) for k in ("name","metaTitle","metaDescription")},
    "after":{k:field(new,k) for k in ("name","metaTitle","metaDescription")},
    "oldHtmlSha":sha(old),"newHtmlSha":sha(field(new,"fullDescription")),
    "imageTagsIdentical":len(re.findall(r"<img\b[^>]*>",old,re.I)),
    "beforeLinkTargets":oldlinks,"afterLinkTargets":anchor_hrefs(field(new,"fullDescription"))})
   (DEST/"deployment-stage2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
   print(json.dumps({"id":id,"state":"APPLIED_VERIFIED","images":row["imageTagsIdentical"],
    "linksBefore":len(oldlinks),"linksAfter":len(row["afterLinkTargets"])},ensure_ascii=False))
 except Exception as e:
  report.append({"status":"ERROR","error":str(e)[:400]})
  (DEST/"deployment-stage2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
  raise
if __name__=="__main__":main()
