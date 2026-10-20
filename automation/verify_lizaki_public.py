import requests, re, json, time
URL="https://papiernia.net.pl/lizaki-swiateczne"
verify_url=URL+"?seo_verify=20261020"
r=requests.get(verify_url,headers={"Cache-Control":"no-cache","Pragma":"no-cache","User-Agent":"PapierniaSEO-Verify/1.0"},timeout=30)
r.raise_for_status()
html=r.text

checks={
  "new_heading":"Lizaki świąteczne na Boże Narodzenie" in html,
  "internal_link":"https://papiernia.net.pl/upominki-swiateczne" in html,
  "year_2026":"Bożego Narodzenia 2026" in html,
  "year_2027":"Nowym Roku 2027" in html or "2027 roku" in html,
  "old_2025_absent":"Nowym Roku 2025" not in html,
  "img5":"/images/uploaded/nowe_zdjecia/swiateczne_lizaki_podziekowania_logo (5).webp" in html,
  "img4":"/images/uploaded/nowe_zdjecia/swiateczne_lizaki_podziekowania_logo (4).webp" in html,
  "google_img":"https://papiernia.net.pl/images/uploaded/google-Copy-1.jpg" in html,
  "line_img":"https://papiernia.net.pl/images/uploaded/linia.png" in html,
  "contact_img":"%E2%80%94Pngtree%E2%80%94black%20mobile%20phone%20and%20phone_4977141.png" in html,
}
print("PUBLIC_VERIFY="+json.dumps({"status":r.status_code,"finalUrl":r.url,"checks":checks,"all":all(checks.values())},ensure_ascii=False))
if not all(checks.values()):
    raise RuntimeError("Public page verification failed")
