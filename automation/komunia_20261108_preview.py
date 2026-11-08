"""Preview ONLY: SEO Komunia category + two P1 products (API 3.0).
No commit/write endpoint is called. Keep all IMG tags and links byte-identical.
"""
import hashlib,json,os,pathlib,re,requests
ROOT="https://papiernia.net.pl/papiernia-seo-api/v3"
KEY=os.environ["PAPIERNIA_SEO_API_KEY"]
session=requests.Session()
session.headers.update({"X-Papiernia-SEO-Key":KEY,"Accept":"application/json"})
TARGETS=[
 {"id":17,"type":"Category","sha":"4244c08f60bcb4863245d203d6d396acd2b499ca08c81c4b96f44e397f4cec87",
  "metaTitle":"Podziękowania dla gości na Komunię – upominki | Papiernia",
  "metaDescription":"Podziękowania dla gości na Komunię: świeczki, magnesy, czekoladki, karmelki i herbatki z personalizacją. Poznaj wzory i wybierz upominki komunijne.",
  "replacements":[]},
 {"id":4897,"type":"Product","sha":"9ee238be03c2b0ed135c21ae76b96ace4eea00ac67eabee8b6f2eab795e0b91c",
  "name":"Świeczka serce w różowym pudełeczku na Komunię",
  "metaTitle":"Świeczka serce w różowym pudełku na Komunię | Papiernia",
  "metaDescription":"Podziękowanie dla gości na Komunię: biała świeczka serce w różowym pudełeczku w złote kropki, z personalizowaną etykietą. Zestaw do złożenia, od 30 szt.",
  "replacements":[
   ["<h2 style=\"text-align: center;\">Oryginalne podziękowania dla Gości komunijnych&nbsp;</h2>",
    "<h2 style=\"text-align: center;\">Świeczka serce w różowym pudełeczku na Komunię – podziękowanie dla gości</h2>"],
   ["<p style=\"text-align: center;\">Drobne personalizowane prezenty dla gości komunijnych wraz z osobistą dedykacją, stała się obecnie powszechnym sposobem podziękowania za przybycie na przyjęcie komunijne dziecka. Tego rodzaju drobne symbole są nie tylko zwykłym podziękowaniem, ale także stanowi unikalną pamiątkę tego wyjątkowego dnia.</p>",
    "<p style=\"text-align: center;\">Świeczka w kształcie serca w różowym pudełeczku w złote kropki to eleganckie podziękowanie dla gości na Pierwszą Komunię Świętą. Personalizowana etykieta z imieniem dziecka, datą uroczystości i krótką dedykacją sprawia, że ten niewielki upominek staje się wyjątkową pamiątką komunijnego przyjęcia.</p>"]]},
 {"id":4912,"type":"Product","sha":"2eed2cbdef3f4e789869731dce3cddfc7d5e16369cefaa522ffdb8a7d387fa19",
  "name":"Karmelki na Komunię – słodkie podziękowanie dla gości",
  "metaTitle":"Karmelki na Komunię – podziękowania dla gości | Papiernia",
  "metaDescription":"Słodkie podziękowania dla gości na Komunię: trzy karmelki z sercem w torebeczce z personalizowaną etykietą. Wybierz wzór i tekst podziękowania. Od 30 szt.",
  "replacements":[
   ["<h2 style=\"text-align: center;\">Słodkie podziękowania komunijne&nbsp;</h2>",
    "<h2 style=\"text-align: center;\">Karmelki na Komunię – słodkie podziękowania dla gości</h2>"],
   ["<p style=\"text-align: center;\">Upominki na słodko z personalizacją to wyjątkowy sposób na podziękowania komunijne dla zaproszonych gości. Taki drobny preznecik&nbsp; zostaje w pamięci na długo. W dniu Pierwszej Komunii Świętej każdy szczegół ma znaczenie. Dlatego warto wybrać coś, co doda uroku temu wyjątkowemu wydarzeniu - cukierki karmelki świetnie się tu sprawdzą&nbsp;</p>",
    "<p style=\"text-align: center;\">Trzy deserowe karmelki z sercem w personalizowanej torebeczce to słodki upominek dla gości na Pierwszą Komunię Świętą. Na etykiecie możesz umieścić imię dziecka, datę przyjęcia i krótkie podziękowanie za obecność. Tak przygotowane karmelki komunijne są drobnym, ale osobistym gestem wdzięczności dla rodziny i przyjaciół.</p>"]]}
]
def get(url):
 r=session.get(url,timeout=35);r.raise_for_status();return r.json()
def field(record,key):
 return record.get(key,record.get(key[0].upper()+key[1:]))
def snapshot(t):
 r=get(f"{ROOT}/{t['type']}Snapshot/{t['id']}")
 return r.get("data",r.get("snapshot",r))
def guarded_new(t,current):
 key="description" if t["type"]=="Category" else "fullDescription"
 html=field(current,key) or ""
 assert hashlib.sha256(html.encode()).hexdigest()==t["sha"],"HTML changed; abort"
 result=html
 for before,after in t["replacements"]:
  assert result.count(before)==1,"Source snippet mismatch; abort"
  result=result.replace(before,after)
 assert re.findall("<img[^>]*>",html,re.I)==re.findall("<img[^>]*>",result,re.I)
 assert re.findall("<a[^>]*>",html,re.I)==re.findall("<a[^>]*>",result,re.I)
 payload={k:t[k] for k in ("name","metaTitle","metaDescription") if k in t}
 if t["replacements"]:payload["fullDescription"]=result
 payload["reason"]="Komunia SEO stage 1 - preview only, preserve all images and URLs"
 return payload,html,result
def main():
 output=pathlib.Path("audit/komunia-20261108");output.mkdir(parents=True,exist_ok=True)
 results=[]
 for t in TARGETS:
  record={"type":t["type"],"id":t["id"]}
  try:
   current=snapshot(t)
   payload,old,new=guarded_new(t,current)
   response=session.post(f"{ROOT}/Preview{t['type']}Seo/{t['id']}",json=payload,timeout=50)
   response.raise_for_status()
   data=response.json()
   if data.get("success") is False or data.get("ok") is False:raise RuntimeError("Preview API reported failure")
   # NEVER log returned approvalToken, which is short-lived and operation scoped.
   record.update({"status":"PREVIEW_OK","changedFields":list(payload),
      "before":{k:field(current,k) for k in ("name","metaTitle","metaDescription")},
      "after":{k:v for k,v in payload.items() if k not in ("fullDescription","reason")},
      "beforeHtmlSha256":hashlib.sha256(old.encode()).hexdigest(),
      "afterHtmlSha256":hashlib.sha256(new.encode()).hexdigest(),
      "imgTagsPreserved":len(re.findall("<img[^>]*>",old,re.I)),
      "linkTagsPreserved":len(re.findall("<a[^>]*>",old,re.I)),
      "previewResultKeys":[x for x in data.keys() if x!="approvalToken"]})
  except Exception as exc:
   record["status"]="ERROR";record["error"]=str(exc)[:250]
  results.append(record)
  print(json.dumps({k:v for k,v in record.items() if k not in ("before","after")},ensure_ascii=False))
 (output/"preview-report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
 if any(x["status"]=="ERROR" for x in results):raise RuntimeError("One or more previews failed. NO production commits were made.")
if __name__=="__main__":main()
