import json, os, re, requests
from pathlib import Path
from datetime import datetime, timezone

BASE="https://papiernia.net.pl/papiernia-seo-api/v1"
KEY=os.environ["PAPIERNIA_SEO_API_KEY"]
HEADERS={"X-Papiernia-SEO-Key":KEY,"Content-Type":"application/json"}
URL="https://papiernia.net.pl/lizaki-swiateczne"
EXPECTED_ID=4919
EXPECTED_NAME="Lizaki świąteczne"
EXPECTED_SLUG="lizaki-swiateczne"

NEW_HTML = r'''<h2 style="text-align: center;"><span style="font-size: 16pt;">Lizaki świąteczne na Boże Narodzenie – drobny upominek dla klientów i firm</span></h2>
<p style="text-align: center;">Lizaki świąteczne to prosty i efektowny sposób na przygotowanie drobnego upominku z okazji Bożego Narodzenia. Biało-czerwony lizak z personalizowaną etykietą może być wręczany klientom, kontrahentom i pracownikom jako słodkie podziękowanie za współpracę, zakupy lub wspólnie spędzony rok. To nieduży prezent, który łatwo dopasować do identyfikacji firmy i charakteru świątecznej akcji.</p>
<p style="text-align: center;">Jeśli szukasz większego wyboru produktów dla biznesu, zobacz również <a href="https://papiernia.net.pl/upominki-swiateczne" title="Upominki świąteczne dla klientów i firm">upominki świąteczne dla klientów i firm</a>.</p>
<p style="text-align: center;">&nbsp;</p>
<p style="text-align: center;"><img src="/images/uploaded/nowe_zdjecia/swiateczne_lizaki_podziekowania_logo (5).webp" alt="Świąteczne lizaki - upominek z logo na święta " width="auto" height="auto" /></p>
<h2 style="text-align: center;"><span style="font-size: 16pt;">Lizaki świąteczne z logo i personalizowaną etykietą</span></h2>
<p style="text-align: center;">Etykietę możemy dopasować do Twojej firmy bez dodatkowych kosztów personalizacji. Do wyboru są gotowe świąteczne motywy graficzne, które można uzupełnić o logo, podpis oraz własny tekst. Dzięki temu lizaki świąteczne z logo sprawdzą się zarówno jako firmowe podziękowanie, jak i niewielki dodatek do zamówienia, prezentu lub spotkania świątecznego.</p>
<p style="text-align: center;">Na etykiecie mogą znaleźć się także lizaki z życzeniami świątecznymi – krótkimi, formalnymi albo bardziej osobistymi, zależnie od odbiorcy.</p>
<h3 style="text-align: center;">Dla kogo sprawdzą się lizaki na Boże Narodzenie?</h3>
<p style="text-align: center;">To dobry wybór jako słodkie podziękowania dla klientów po zakupie lub wykonanej usłudze, drobne upominki świąteczne dla kontrahentów oraz niewielki prezent dla pracowników podczas firmowej wigilii lub spotkania kończącego rok.</p>
<h3 style="text-align: center;">Przykładowe życzenia na Boże Narodzenie 2026 i Nowy Rok 2027</h3>
<p style="text-align: center;"><strong><em>„Radosnych Świąt Bożego Narodzenia 2026 oraz pomyślności w Nowym Roku 2027 życzy [nazwa firmy]”</em></strong></p>
<p style="text-align: center;"><strong><em>„Dziękujemy za zaufanie i współpracę. Spokojnych Świąt Bożego Narodzenia 2026 oraz wielu sukcesów w 2027 roku życzy [nazwa firmy]”</em></strong></p>
<p style="text-align: center;"><strong><em>„Serdeczne życzenia zdrowych i radosnych Świąt Bożego Narodzenia oraz szczęśliwego Nowego Roku 2027 składa [nazwa firmy]”</em></strong></p>
<p style="text-align: center;"><strong><em>„Dziękujemy za wspólny rok. Wesołych Świąt i wszystkiego dobrego w 2027 roku życzy [nazwa firmy]”</em></strong></p>
<p style="text-align: center;">&nbsp;</p>
<p style="text-align: center;"><img src="/images/uploaded/nowe_zdjecia/swiateczne_lizaki_podziekowania_logo (4).webp" alt="Świąteczne lizaki - upominek z logo na świeta" width="auto" height="auto" /></p>
<h2 style="text-align: center;"><span style="font-size: 16pt;">Jak zamówić personalizowane lizaki świąteczne?</span></h2>
<p style="text-align: center;">1. Podaj tekst i dane do personalizacji – możesz również przesłać logo firmy.<br />
2. Wybierz wzór graficzny dostępny w zakładce z modelami graficznymi lub w galerii.<br />
3. Dodaj do koszyka potrzebną liczbę sztuk – minimalne zamówienie wynosi 30 sztuk.<br />
4. Przejdź do koszyka i dokończ proces zamówienia.</p>
<p style="text-align: center;">W ten sposób otrzymasz lizaki na Boże Narodzenie dopasowane do firmy, odbiorców i wybranego tekstu życzeń.</p>
<p style="text-align: center;">&nbsp;</p>
<p style="text-align: center;"><strong>Zaufaj marce z 12 letnim doświadczeniem i 100% pozytywnych opinii w google</strong></p>
<p style="text-align: center;"><strong><a title="papiernia.net.pl" href="https://g.co/kgs/1KtJoWz"><img src="https://papiernia.net.pl/images/uploaded/google-Copy-1.jpg" alt="papiernia.net.pl opinie" width="40" height="40" /></a></strong></p>
<p style="text-align: center;"><strong><a title="papiernia.net.pl" href="https://g.co/kgs/1KtJoWz"><img src="https://papiernia.net.pl/images/uploaded/linia.png" alt="" width="auto" height="auto" /></a></strong></p>
<p style="text-align: center;"><strong>Masz pytania? Skontaktuj się z nami</strong></p>
<p><strong><a title="papiernia.net.pl - kontakt" href="https://papiernia.net.pl/contactus"><img style="display: block; margin-left: auto; margin-right: auto;" src="https://papiernia.net.pl/images/uploaded/%E2%80%94Pngtree%E2%80%94black%20mobile%20phone%20and%20phone_4977141.png" alt="papiernia.net.pl kontakt" width="40" height="40" /></a></strong></p>'''

def get(path, params=None):
    r=requests.get(f"{BASE}/{path}",headers={"X-Papiernia-SEO-Key":KEY},params=params,timeout=30)
    r.raise_for_status()
    return r.json()

def put(path,payload,dry_run):
    r=requests.put(f"{BASE}/{path}",headers=HEADERS,params={"dryRun":"true" if dry_run else "false"},json=payload,timeout=45)
    r.raise_for_status()
    return r.json()

resolved=get("Resolve",{"url":URL})
if resolved.get("entity")!="Product" or int(resolved.get("id",0))!=EXPECTED_ID:
    raise RuntimeError(f"Wrong product resolved: {resolved}")
if resolved.get("Name")!=EXPECTED_NAME or resolved.get("slug")!=EXPECTED_SLUG:
    raise RuntimeError(f"Product identity mismatch: {resolved}")
if not resolved.get("Published") or resolved.get("Deleted"):
    raise RuntimeError(f"Product is not safe to update: {resolved}")

before=get(f"Product/{EXPECTED_ID}")
if before.get("Name")!=EXPECTED_NAME or before.get("SeName")!=EXPECTED_SLUG:
    raise RuntimeError("Product identity changed between resolve and read")

old_html=before.get("FullDescription") or ""
img_pattern=re.compile(r"<img\b[^>]*>",re.I)
old_imgs=img_pattern.findall(old_html)
new_imgs=img_pattern.findall(NEW_HTML)
if old_imgs != new_imgs:
    raise RuntimeError("Image tags differ between old and new HTML; aborting")
if len(old_imgs)!=5:
    raise RuntimeError(f"Unexpected image count: {len(old_imgs)}")

immutable_before={
    "Name":before.get("Name"),
    "SeName":before.get("SeName"),
    "ShortDescription":before.get("ShortDescription"),
    "MetaTitle":before.get("MetaTitle"),
    "MetaDescription":before.get("MetaDescription"),
    "MetaKeywords":before.get("MetaKeywords"),
    "Published":before.get("Published"),
    "Deleted":before.get("Deleted"),
}

request_id="auto-seo-lizaki-swiateczne-20261020-full-description"
payload={
    "FullDescription":NEW_HTML,
    "RequestId":request_id,
    "Reason":"SEO pełnego opisu produktu Lizaki świąteczne: język, frazy, życzenia 2026/2027, sposób zamawiania i link wewnętrzny. Tylko FullDescription."
}

dry=put(f"UpdateProduct/{EXPECTED_ID}",payload,True)
if not dry.get("ok") or not dry.get("dryRun"):
    raise RuntimeError(f"Dry-run failed: {dry}")

applied=put(f"UpdateProduct/{EXPECTED_ID}",payload,False)
if not applied.get("ok") or applied.get("dryRun"):
    raise RuntimeError(f"Apply failed: {applied}")

after=get(f"Product/{EXPECTED_ID}")
if after.get("FullDescription") != NEW_HTML:
    raise RuntimeError("Post-write FullDescription mismatch")

immutable_after={k:after.get(k) for k in immutable_before}
if immutable_before != immutable_after:
    raise RuntimeError(f"Unexpected immutable field change: before={immutable_before}, after={immutable_after}")

after_imgs=img_pattern.findall(after.get("FullDescription") or "")
if after_imgs != old_imgs:
    raise RuntimeError("Image tags changed after write")

Path("reports").mkdir(exist_ok=True)
Path("reports/lizaki-swiateczne-after.html").write_text(after["FullDescription"],encoding="utf-8")
Path("reports/lizaki-swiateczne-deploy.json").write_text(json.dumps({
    "utc":datetime.now(timezone.utc).isoformat(),
    "url":URL,
    "id":EXPECTED_ID,
    "name":EXPECTED_NAME,
    "dryRun":dry,
    "applied":applied,
    "immutableFieldsVerified":True,
    "imageTagsVerified":True,
    "imageCount":len(after_imgs),
    "internalLinkPresent":"https://papiernia.net.pl/upominki-swiateczne" in after["FullDescription"],
    "contains2025":"2025" in after["FullDescription"],
    "contains2026":"2026" in after["FullDescription"],
    "contains2027":"2027" in after["FullDescription"]
},ensure_ascii=False,indent=2),encoding="utf-8")

print("DEPLOY_RESULT="+json.dumps({
    "id":EXPECTED_ID,
    "name":EXPECTED_NAME,
    "url":URL,
    "ok":True,
    "onlyFullDescriptionChanged":True,
    "imageTagsVerified":True,
    "imageCount":len(after_imgs),
    "internalLinkPresent":"https://papiernia.net.pl/upominki-swiateczne" in after["FullDescription"],
    "contains2025":"2025" in after["FullDescription"],
    "contains2026":"2026" in after["FullDescription"],
    "contains2027":"2027" in after["FullDescription"],
    "updatedOnUtc":after.get("UpdatedOnUtc")
},ensure_ascii=False))
