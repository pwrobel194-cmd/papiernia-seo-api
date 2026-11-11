import os, json, re, pathlib, hashlib, requests, html
from datetime import datetime, timezone

BASE = "https://papiernia.net.pl"
API = BASE + "/papiernia-seo-api"
HEADER = {"X-Papiernia-SEO-Key": os.environ["PAPIERNIA_SEO_API_KEY"]}
MODE = os.environ.get("SEO_ACTION", "preview").lower()
assert MODE in {"preview","apply"}
REASON = "Zlecone przez właściciela 2026-11-11: porządek SEO podkategorii ciasteczek weselnych, H1/meta/opisy i linkowanie; bez zmiany URL, zdjęć i cen"
OUT = pathlib.Path("reports/wesele-cookies-deployment")
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers.update(HEADER)

def call(method, route, data=None):
    kw={"timeout":60}
    if data is not None: kw["json"]=data
    r=S.request(method,API+route,**kw)
    if r.status_code>=400:
        raise RuntimeError(f"{method} {route}: HTTP {r.status_code}: {r.text[:400]}")
    j=r.json()
    if j.get("ok") is False: raise RuntimeError(f"{route}: {j.get('error') or str(j)[:200]}")
    return j

def image_sources(s):
    tags=re.findall(r"<img\b[^>]*>", s or "", re.I)
    return [m.group(1) if (m:=re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']',tag,re.I)) else None for tag in tags]

def sha(s): return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

CATEGORY = """
<div style="width:100%;max-width:none;line-height:1.75;">
<h2>Ciasteczka z wróżbą na wesele – oryginalne podziękowania dla gości</h2>
<p><strong>Ciasteczka z wróżbą na wesele</strong>, nazywane także ciasteczkami szczęścia, to drobny, słodki upominek, który można położyć przy nakryciu każdego gościa lub wręczyć po ceremonii ślubnej. Kruche ciasteczko o delikatnym waniliowym smaku skrywa karteczkę z niespodzianką. Dzięki personalizowanej oprawie staje się jednocześnie pamiątką uroczystości i podziękowaniem za przybycie.</p>
<p>W Papierni przygotowujemy kilka rodzajów <strong>podziękowań weselnych z ciasteczkiem z wróżbą</strong>: od minimalistycznych bilecików po pudełeczka, ozdobne torebki i wariant z winietką 2w1. Poniżej poznasz różnice między nimi i wybierzesz styl pasujący do przyjęcia – rustykalnego, klasycznego, romantycznego lub glamour.</p>

<h2>Wybierz ciasteczko z wróżbą dla gości weselnych</h2>
<h3>Ciasteczko z wróżbą i winietką 2w1</h3>
<p><a href="/podziekowania-dla-gosci-z-winietka" title="Ciasteczko z wróżbą i winietką na wesele">Wariant z personalizowaną winietką</a> łączy podziękowanie z oznaczeniem miejsca przy stole. Przydaje się zwłaszcza wtedy, gdy planujesz konkretny układ miejsc i chcesz ograniczyć liczbę dodatków na nakryciu. Na winietce umieszczamy dane wskazanych gości według przekazanej listy.</p>
<h3>Ciasteczko z wróżbą w personalizowanej torebce</h3>
<p><a href="/podziekowanie-na-slub-torebka-z-ciasteczkiem-z-wrozba" title="Ciasteczka z wróżbą w torebkach weselnych">Torebka z ciasteczkiem</a> ma formę niewielkiego, gotowego upominku z ozdobnym bilecikiem, krótkim tekstem podziękowania, imionami Pary Młodej i datą ślubu. To wygodny sposób na przygotowanie jednakowych prezencików dla zaproszonych osób.</p>
<h3>Ciasteczko z wróżbą w białym pudełeczku</h3>
<p><a href="/ciasteczka-z-wrozba-na-podziekowania" title="Ciasteczko w białym pudełeczku na wesele">Białe pudełeczko 5 × 5 × 5 cm</a> sprawdzi się na klasycznym przyjęciu. Do zestawu dołączamy personalizowaną etykietę. Pudełeczka otrzymujesz rozłożone, a etykiety na arkuszach <strong>do samodzielnego złożenia i naklejenia</strong>.</p>
<h3>Ciasteczko w pudełeczku EKO na wesele</h3>
<p><a href="/podziekowania-dla-gosci-ciasteczko-z-wrozba" title="Rustykalne ciasteczko z wróżbą w pudełku EKO">Brązowe pudełeczko EKO 5 × 5 × 5 cm</a> podkreśla styl boho i rustykalny. Zestaw obejmuje ciasteczko i personalizowaną etykietę 45 × 45 mm; opakowanie dostarczamy rozłożone, a etykietę do samodzielnego przyklejenia.</p>
<h3>Różowe pudełeczko ze złotymi kropkami</h3>
<p><a href="/ciasteczka-z-wrozba-wesele" title="Ciasteczko z wróżbą w różowym pudełku w złote kropki">Różowe pudełeczko w złote kropki</a> ma po złożeniu około 6 × 3,5 × 5,5 cm. To propozycja dla par szukających bardziej dekoracyjnej oprawy, np. na wesele w stylu glamour. Pudełeczko i etykieta wymagają samodzielnego przygotowania.</p>
<h3>Ciasteczko z wróżbą ze złotym bilecikiem</h3>
<p><a href="/ciasteczka-z-wrozba-slub" title="Ciasteczko ze złotym bilecikiem na ślub">Złoty bilecik</a> nadaje tradycyjnemu ciasteczku odświętny wygląd. Bilecik ma wymiary około 7 × 7 cm, a biała etykieta z nadrukiem 6,3 × 6,3 cm. Ten wariant sprawdzi się, jeśli wolisz smukły upominek bez pudełeczka.</p>

<h2>Co znajduje się w ciasteczkach szczęścia?</h2>
<p>Wewnątrz kruchego, lekko waniliowego ciasteczka znajduje się mała karteczka z wróżbą. Teksty są uniwersalne i losowo dobierane z dostępnej puli – nie są to indywidualne wróżby przygotowane dla każdego gościa. Dzięki temu otwieranie ciasteczek jest miłym, zaskakującym elementem przyjęcia i może stać się pretekstem do rozmowy przy stole.</p>
<h3>Przykładowe teksty wróżb</h3>
<ul>
<li>Nigdy nie wątp w siebie, a wygrasz.</li>
<li>Nowe horyzonty otworzą się przed Tobą w przyszłym miesiącu.</li>
<li>Wkrótce wydarzy się coś, co bardzo Cię zaskoczy.</li>
<li>Dziś gwiazdy mówią, że dostaniesz wszystko, czego chcesz.</li>
<li>Przed Tobą przyjemne doświadczenie – nie przegap go.</li>
<li>Zaufaj swojej intuicji, a odniesiesz sukces.</li>
<li>Czekają na Ciebie nowe perspektywy.</li>
</ul>
<p>Losowa treść wewnątrz ciasteczka jest niezależna od personalizacji zewnętrznego opakowania. Dzięki temu każdy gość otrzymuje podziękowanie z Waszymi danymi i jednocześnie własną niespodziankę.</p>

<h2>Personalizowane podziękowania na ślub – imiona, data i grafika</h2>
<p>Wybrane warianty umożliwiają dodanie imion Pary Młodej, daty wesela, krótkich życzeń lub tekstu podziękowania i dopasowanego wzoru graficznego. Personalizacja etykiet jest uwzględniona w cenie produktu zgodnie z jego opisem. Możesz użyć klasycznego „Dziękujemy za przybycie”, nawiązać do motywu przewodniego wesela lub wybrać krótkie, nieformalne hasło.</p>
<p>Przykładowe napisy na bilecik: „Dziękujemy, że jesteś dziś z nami”, „Dziękujemy za Twoją obecność” albo „Za przybycie dziękujemy, ciastkiem z wróżbą częstujemy”. Tekst warto ograniczyć do kilku słów, by nadruk pozostał czytelny. W przypadku wariantu z winietką potrzebna jest także lista imion i nazwisk gości.</p>
<p>W niektórych zestawach opakowania i naklejki dostarczane są oddzielnie <strong>do samodzielnego złożenia</strong>. Informacja o zawartości, wymiarach i sposobie przygotowania znajduje się na stronie każdego produktu – przed zamówieniem sprawdź wybrany wariant.</p>

<h2>Jak wykorzystać ciasteczka z wróżbą podczas wesela?</h2>
<p><strong>Przy nakryciu:</strong> pudełeczko lub torebka obok talerza tworzy gotowy element dekoracji stołu. <strong>W połączeniu z winietką:</strong> upominek od razu wskazuje gościowi miejsce. <strong>Przy pożegnaniu:</strong> ciasteczko z podziękowaniem można wręczyć po zakończeniu uroczystości. <strong>W strefie upominków:</strong> kilka wariantów opakowań może współgrać z motywem dekoracyjnym przyjęcia.</p>
<p>Jeżeli planujesz inny styl opakowania, np. romantyczny motyw serca, porównaj także inne produkty w dziale <a href="/upominki-i-podziekowania-dla-gosci-weselnych" title="Wszystkie podziękowania na wesele">podziękowania dla gości weselnych</a>. Tutaj skupiamy się na sześciu aktualnych wariantach ciasteczek z wróżbą.</p>

<h2>Jak zamówić ciasteczka z wróżbą na wesele?</h2>
<ol>
<li>Wybierz jeden z wariantów powyżej i sprawdź dokładną zawartość zestawu.</li>
<li>W zakładce „Modele graficzne” wybierz projekt nadruku.</li>
<li>Podaj krótki tekst podziękowania, imiona oraz datę ślubu; przy winietkach dołącz listę gości.</li>
<li>Dodaj do koszyka potrzebną ilość – standardowe minimum to 30 sztuk.</li>
<li>Dokończ zamówienie; szczegóły realizacji oraz przygotowania zestawu znajdują się przy wybranym produkcie.</li>
</ol>

<h2>Najczęściej zadawane pytania o ciasteczka z wróżbą na wesele</h2>
<h3>Czy można zmienić treść wróżby wewnątrz ciasteczka?</h3>
<p>Wróżby wewnątrz ciasteczek są dobierane losowo z puli tekstów. Personalizacji podlega przede wszystkim nadruk na bileciku, etykiecie lub opakowaniu – zależnie od wersji.</p>
<h3>Jakie opakowanie najlepiej pasuje do stylu wesela?</h3>
<p>Na przyjęcia rustykalne polecamy pudełeczko EKO, do klasycznych aranżacji – białe, a do stylu glamour – różowe w złote kropki lub wariant ze złotym bilecikiem. Gdy zależy Ci na oznaczeniu miejsc, wybierz ciasteczko z winietką 2w1.</p>
<h3>Czy pudełeczka są już złożone?</h3>
<p>Warianty pudełeczkowe opisane w tej kategorii mają opakowania dostarczane rozłożone, a etykiety przeznaczone do samodzielnego naklejenia. Dokładny sposób przygotowania należy sprawdzić w opisie konkretnego produktu.</p>
</div>
""".strip()

PROPOSALS = {
"winietka": {
 "id":4904, "name":"Ciasteczko z wróżbą i winietką 2w1 na wesele",
 "metaTitle":"Ciasteczko z wróżbą i winietką 2w1 | Papiernia",
 "metaDescription":"Ciasteczko z wróżbą i winietką 2w1 na wesele. Podziękowanie dla gości i oznaczenie miejsca przy stole w jednym. Personalizowane wzory.",
 "h2":"Ciasteczko z wróżbą i winietką – weselne podziękowanie 2w1",
 "intro":"Ten wariant łączy podziękowanie dla gościa weselnego z imienną winietką na stół. Na bileciku można umieścić krótkie życzenia, a na winietce imię i nazwisko zgodnie z przesłaną listą gości."},
"torebka": {
 "id":4884, "name":"Ciasteczko z wróżbą w torebce na wesele",
 "metaTitle":"Ciasteczko z wróżbą w torebce na wesele | Papiernia",
 "metaDescription":"Ciasteczko z wróżbą w personalizowanej torebce na wesele. Drobne podziękowanie dla gości z imionami Pary Młodej, datą ślubu i wybraną grafiką.",
 "h2":"Ciasteczko z wróżbą w personalizowanej torebce weselnej",
 "intro":"Ciasteczko z wróżbą zamknięte w niewielkiej torebce z personalizowanym bilecikiem to gotowy pomysł na podziękowanie dla gości weselnych. Ten wariant stawia na estetyczną oprawę bez sztywnego pudełeczka."},
"biale": {
 "id":4898, "name":"Ciasteczko z wróżbą w białym pudełeczku na wesele",
 "metaTitle":"Ciasteczko z wróżbą w białym pudełku | Papiernia",
 "metaDescription":"Ciasteczko z wróżbą w białym pudełeczku 5 × 5 × 5 cm z personalizowaną etykietą. Podziękowania dla gości weselnych od 30 sztuk, do złożenia.",
 "h2":"Ciasteczko z wróżbą w białym pudełeczku – prezent dla gości",
 "intro":"Zestaw obejmuje kruche ciasteczko z losową wróżbą, białe pudełeczko 5 × 5 × 5 cm i etykietę z personalizowanym nadrukiem. Opakowanie jest dostarczane rozłożone, a etykietę przykleja się samodzielnie."},
"eko": {
 "id":4899, "name":"Ciasteczko z wróżbą w pudełeczku EKO na wesele",
 "metaTitle":"Ciasteczko z wróżbą w pudełku EKO | Papiernia",
 "metaDescription":"Rustykalne podziękowanie na wesele: ciasteczko z wróżbą w brązowym pudełeczku EKO 5 × 5 × 5 cm, z personalizowaną etykietą do naklejenia.",
 "h2":"Rustykalne ciasteczko z wróżbą w pudełeczku EKO",
 "intro":"Brązowe pudełeczko EKO o wymiarach 5 × 5 × 5 cm nadaje ciasteczku z wróżbą naturalny charakter, dlatego pasuje do przyjęć rustykalnych i boho. Zestaw zawiera etykietę z własnym nadrukiem do samodzielnego naklejenia."},
"rozowe": {
 "id":4888, "name":"Ciasteczko z wróżbą w różowym pudełeczku na wesele",
 "metaTitle":"Ciasteczko w różowym pudełku na wesele | Papiernia",
 "metaDescription":"Ciasteczko z wróżbą w różowym pudełeczku ze złotymi kropkami. Personalizowany prezencik dla gości weselnych w stylu glamour.",
 "h2":"Ciasteczko z wróżbą w różowym pudełeczku w złote kropki",
 "intro":"Różowe pudełeczko ozdobione złotymi kropkami ma po złożeniu około 6 × 3,5 × 5,5 cm. Zawiera ciasteczko z wróżbą; etykietę z wybranym wzorem i krótkim podziękowaniem należy nakleić samodzielnie."},
"bilecik": {
 "id":4900, "name":"Ciasteczko z wróżbą ze złotym bilecikiem na ślub",
 "metaTitle":"Ciasteczko z wróżbą ze złotym bilecikiem | Papiernia",
 "metaDescription":"Ciasteczko z wróżbą ze złotym bilecikiem 7 × 7 cm i personalizowaną etykietą. Eleganckie podziękowanie dla gości weselnych.",
 "h2":"Ciasteczko z wróżbą ze złotym bilecikiem na ślub",
 "intro":"W tej wersji ciasteczko z wróżbą łączy się ze złotym bilecikiem o wymiarach 7 × 7 cm i białą etykietą 6,3 × 6,3 cm. Błyszczący papier stanowi elegancką alternatywę dla pudełeczka."},
}
CAT_PROPOSAL={
 "name":"Ciasteczka z wróżbą na wesele – podziękowania dla gości",
 "metaTitle":"Ciasteczka z wróżbą na wesele – dla gości | Papiernia",
 "metaDescription":"Ciasteczka z wróżbą na wesele jako podziękowania dla gości. W pudełkach, torebkach, z winietką 2w1 lub złotym bilecikiem. Wybierz personalizację.",
 "description":CATEGORY
}
BACKLINK='<p style="margin:20px 0;text-align:center;">Sprawdź także <a href="/ciasteczka-z-wrozba-dla-gosci-na-wesele" title="Wszystkie ciasteczka z wróżbą na wesele">wszystkie warianty ciasteczek z wróżbą na wesele</a> – pudełeczka, torebki, winietki i bileciki.</p>'

def change_html(old,label,data):
    h2=f'<h2 style="text-align:center;">{html.escape(data["h2"])}</h2>'
    new,n=re.subn(r'<h2\b[^>]*>[\s\S]*?</h2\s*>',lambda _:h2,old,count=1,flags=re.I)
    if n!=1: raise RuntimeError(label+" has no H2")
    intro='<p style="text-align:center;line-height:1.7;">'+html.escape(data["intro"])+'</p>'
    new=re.sub(r'(</h2\s*>)',lambda m:m.group(1)+"\n"+intro,new,count=1,flags=re.I)
    if "/ciasteczka-z-wrozba-dla-gosci-na-wesele" not in new: new+="\n"+BACKLINK
    new=new.replace("elegankim pudełeczku","eleganckim pudełeczku")
    return new

def all_fields(before, after, fields):
    return {f:{"before":before.get(f),"after":after.get(f)} for f in fields if before.get(f)!=after.get(f)}

report={"mode":MODE,"timestamp":datetime.now(timezone.utc).isoformat(),"entries":[]}
backups={}
route="/v3/CategorySnapshot/362"
category=call("GET",route)
assert category["slug"]=="ciasteczka-z-wrozba-dla-gosci-na-wesele" and category["Published"] and not category["Deleted"]
backups["category"]=category
old_cat=category["Description"] or ""
if image_sources(old_cat)!=image_sources(CATEGORY): raise RuntimeError("Category image mismatch")
if len(re.sub(r'<[^>]*>',"",CATEGORY)) < len(re.sub(r'<[^>]*>',"",old_cat))*0.9: raise RuntimeError("New category copy unexpectedly shortened")
for label, data in PROPOSALS.items():
    d=call("GET","/v3/ProductSnapshot/"+str(data["id"]))
    assert d["Published"] and not d["Deleted"] and 362 in d["categoryIds"],label+" not assigned to category 362"
    backups[label]=d

(OUT/"before.json").write_text(json.dumps(backups,ensure_ascii=False,indent=2),encoding="utf-8")

tasks=[("category",362,CAT_PROPOSAL)]
for label,data in PROPOSALS.items():
    current=backups[label]
    full=change_html(current["FullDescription"],label,data)
    assert image_sources(full)==image_sources(current["FullDescription"]), label+" images changed"
    # Restrict edits to H1, HTML, Meta Title/Description. All other fields untouched.
    tasks.append((label,data["id"],{
        "name":data["name"],"metaTitle":data["metaTitle"],
        "metaDescription":data["metaDescription"],"fullDescription":full
    }))

for label, id, data in tasks:
    kind="Category" if label=="category" else "Product"
    original=backups[label]
    mapped={"name":original["name"],"metaTitle":original["MetaTitle"],"metaDescription":original["MetaDescription"]}
    if label=="category": mapped["description"]=original["Description"]
    else: mapped["fullDescription"]=original["FullDescription"]
    delta=all_fields(mapped,data,list(data.keys()))
    entry={"item":label,"id":id,"url":BASE+"/"+original["slug"],
           "fields_changed":list(delta),
           "before":{k:sha(v["before"]) if k in ("description","fullDescription") else v["before"] for k,v in delta.items()},
           "after":{k:sha(v["after"]) if k in ("description","fullDescription") else v["after"] for k,v in delta.items()},
           "images_preserved":image_sources(mapped.get("description" if label=="category" else "fullDescription","")) == image_sources(data.get("description" if label=="category" else "fullDescription",""))}
    # Don't save signed approval tokens.
    route=f"/v3/Preview{kind}Seo/{id}"
    preview=call("POST",route,data)
    if not preview.get("dryRun") or not preview.get("approvalToken"): raise RuntimeError("Missing verified preview token")
    entry["preview"]="ok"
    if MODE=="apply":
        payload={**data,"approvalToken":preview["approvalToken"],"reason":REASON}
        result=call("PUT",f"/v3/Commit{kind}Seo/{id}",payload)
        entry["commit"]=result
        verified=call("GET",f"/v3/{kind}Snapshot/{id}")
        for key,value in data.items():
            k={"name":"name","metaTitle":"MetaTitle","metaDescription":"MetaDescription","description":"Description","fullDescription":"FullDescription"}[key]
            if verified.get(k)!=value: raise RuntimeError(f"VERIFY FAILED {label} {k}")
        if verified["slug"]!=original["slug"]: raise RuntimeError("Slug changed!")
        imgs_before=image_sources(original.get("Description") or original.get("FullDescription") or "")
        imgs_after=image_sources(verified.get("Description") or verified.get("FullDescription") or "")
        if imgs_before!=imgs_after: raise RuntimeError("Images changed!")
        if label!="category":
            if len(verified["pictures"])!=len(original["pictures"]) or [p["Id"] for p in verified["pictures"]]!=[p["Id"] for p in original["pictures"]]:
                raise RuntimeError("Gallery changed!")
            if verified["categoryIds"]!=original["categoryIds"]:raise RuntimeError("Category assignments changed!")
        entry["verified"]="ok"
    report["entries"].append(entry)
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("RESULT",label,"id",id,"mode",MODE,"fields",",".join(entry["fields_changed"]),"verification",entry.get("verified","preview_only"),flush=True)
print("COMPLETE",MODE,"items",len(report["entries"]))
