#!/usr/bin/env python3
"""One-off, owner-approved live test of Papiernia SEO API v3.

ONLY target: test-swieca-pienkowa-z-etykieta-swieta (test product).
Do not write to any other product. No prices, orders, stock or image files.
Running twice is idempotent (second pass should do no writes).
"""
import html
import json
import os
import pathlib
import re
import sys
import traceback

import requests

BASE = "https://papiernia.net.pl/papiernia-seo-api"
OLD_SLUG = "test-swieca-pienkowa-z-etykieta-swieta"
NEW_SLUG = "test-kot-w-butach-api-v3"
PRODUCT_URL = "https://papiernia.net.pl/" + OLD_SLUG
REPORT = pathlib.Path("test-results/seo-api-v3-kot-w-butach.json")
KEY = os.environ.get("PAPIERNIA_SEO_API_KEY", "")
if not KEY:
    raise SystemExit("Missing GitHub Actions secret PAPIERNIA_SEO_API_KEY")

session = requests.Session()
session.headers.update({"X-Papiernia-SEO-Key": KEY, "Accept": "application/json"})
report = {"target": PRODUCT_URL, "purpose": "Owner-approved test of SEO API v3", "steps": []}

def save():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

def api(method, endpoint, **kwargs):
    r = session.request(method, BASE + endpoint, timeout=45, **kwargs)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {endpoint}: HTTP {r.status_code}, body={r.text[:450]}")
    return r.json()

def record(step, data=None):
    report["steps"].append({"step": step, "data": data})
    save()
    print(step, flush=True)

def val(obj, name, default=None):
    return obj.get(name, obj.get(name[0].lower() + name[1:], default))

def images(html_text):
    return re.findall(r"<img\b[^>]*>", html_text or "", flags=re.IGNORECASE)

def make_html_image_gallery(tags):
    if not tags:
        return ""
    return ('<h3>Zdjęcia zachowane z poprzedniej wersji produktu</h3>'
            '<p>Zdjęcia służą jedynie do przetestowania zachowania obrazów '
            'podczas zmiany opisów API.</p>'
            + "\n".join('<p style="text-align:center">' + t + '</p>' for t in tags))

def main():
    health = api("GET", "/v1/Health")
    record("v1 health", {"ok": val(health, "Ok"), "version": val(health, "Version")})
    if val(health, "Ok") is not True:
        raise RuntimeError("Existing v1 API health not OK")

    resolved = None
    for slug in (OLD_SLUG, NEW_SLUG):
        try:
            resolved = api("GET", "/v1/Resolve", params={"url": slug})
            break
        except RuntimeError as exc:
            if "HTTP 404" not in str(exc):
                raise
    if not resolved or str(val(resolved, "Entity")).lower() != "product":
        raise RuntimeError("Target product not resolvable as Product")

    pid = int(val(resolved, "Id"))
    snapshot = api("GET", f"/v3/ProductSnapshot/{pid}")
    current_slug = val(snapshot, "Slug")
    record("Resolved and read v3 ProductSnapshot",
           {"id": pid, "slug": current_slug, "name": val(snapshot, "Name"),
            "published": val(snapshot, "Published"), "deleted": val(snapshot, "Deleted")})

    if current_slug not in (OLD_SLUG, NEW_SLUG) or val(snapshot, "Deleted"):
        raise RuntimeError(f"SAFETY STOP: unexpected product slug {current_slug!r}")
    if str(val(snapshot, "Name", "")).startswith("TEST") and current_slug not in (OLD_SLUG, NEW_SLUG):
        raise RuntimeError("Unexpected test target")

    old_short = val(snapshot, "ShortDescription", "") or ""
    old_full = val(snapshot, "FullDescription", "") or ""
    short_gallery = make_html_image_gallery(images(old_short))
    full_gallery = make_html_image_gallery(images(old_full))
    short = ('''<div style="text-align:center;line-height:1.7">
<p><strong>TEST – Kot w butach</strong> to demonstracyjny upominek z personalizowaną etykietą.
Ten produkt służy wyłącznie do sprawdzenia działania Papiernia SEO API 3.0.</p>
<p><strong>Charakterystyka produktu</strong></p>
<p>Motyw: Kot w butach<br>Personalizacja: przykładowa etykieta<br>
Przeznaczenie: test sklepu, nie oferta sprzedaży<br>
Zestaw: do samodzielnego złożenia</p>
</div>''' + short_gallery)
    full = ('''<div style="line-height:1.7">
<h2>Kot w butach – przykładowy personalizowany upominek</h2>
<p>To fikcyjny produkt testowy, utworzony do sprawdzenia edycji SEO
w sklepie Papiernia.net.pl. Motyw Kota w butach pokazuje, jak można przygotować
opis personalizowanego upominku z etykietą, dedykacją i grafiką.</p>
<h2>Co można spersonalizować?</h2>
<p>W typowej ofercie podobny upominek mógłby otrzymać imię, datę uroczystości,
krótką dedykację i wybrany motyw graficzny. Ten wpis jest wyłącznie demonstracją.</p>
<h3>Charakterystyka wersji testowej</h3>
<ul><li>Motyw: Kot w butach</li>
<li>Rodzaj: personalizowany upominek demonstracyjny</li>
<li>Montaż: do samodzielnego złożenia</li>
<li>Status: produkt testowy – nie należy składać zamówień</li></ul>
<h2>Jak zamówić podobny upominek?</h2>
<ol><li>Wybierz właściwy produkt z oferty Papiernia.net.pl.</li>
<li>Wskaż wzór graficzny i treść personalizacji.</li>
<li>Zatwierdź wizualizację i zrealizuj zamówienie.</li></ol>
<p><strong>Uwaga:</strong> To nie jest rzeczywista oferta produktu Kot w butach.
Wpis służy wyłącznie do testu API 3.0.</p>
</div>''' + full_gallery)
    updates = {
        "name": "TEST – Kot w butach | personalizowany upominek",
        "sku": "TEST-KOT-W-BUTACH-001",
        "shortDescription": short,
        "fullDescription": full,
        "metaTitle": "TEST – Kot w butach | Upominek personalizowany – Papiernia",
        "metaDescription": "Przykładowy produkt TEST – Kot w butach z personalizowaną etykietą. Demonstracja opisów, H1, SKU i SEO w Papiernia API 3.0. To nie jest oferta sprzedaży.",
        "metaKeywords": "kot w butach, produkt testowy, personalizowany upominek",
        "seName": NEW_SLUG,
        "reason": "Zatwierdzony przez właściciela jednorazowy test API 3.0 (2026-11-05)"
    }

    snapshot_before = {
        "id": pid, "name": val(snapshot, "Name"), "sku": val(snapshot, "Sku"),
        "slug": current_slug, "metaTitle": val(snapshot, "MetaTitle"),
        "metaDescription": val(snapshot, "MetaDescription"),
        "shortDescription": old_short, "fullDescription": old_full,
        "pictures": val(snapshot, "Pictures", [])
    }
    report["before"] = snapshot_before
    save()

    if all(val(snapshot, k[0].upper() + k[1:]) == v for k, v in updates.items()
           if k not in ("seName", "reason")) and current_slug == NEW_SLUG:
        record("Content already matches desired state; no write")
    else:
        preview = api("POST", f"/v3/PreviewProductSeo/{pid}", json=updates)
        token = val(preview, "ApprovalToken")
        if not token or val(preview, "DryRun") is not True:
            raise RuntimeError("No valid v3 preview approval token")
        after = val(preview, "After", {})
        if (val(after, "Name") != updates["name"]
            or val(after, "Sku") != updates["sku"]
            or val(after, "SeName") != NEW_SLUG):
            raise RuntimeError("Preview does not match explicitly authorized changes")
        record("PREVIEW passed - no data committed",
               {"productId": pid, "beforeName": val(val(preview, "Before", {}), "Name"),
                "afterName": val(after, "Name"), "newSlug": val(after, "SeName"),
                "shortImagesPreserved": len(images(old_short)),
                "fullImagesPreserved": len(images(old_full))})
        check = api("GET", f"/v3/ProductSnapshot/{pid}")
        if val(check, "UpdatedOnUtc") != val(snapshot, "UpdatedOnUtc"):
            raise RuntimeError("Product unexpectedly changed during preview")
        commit = api("PUT", f"/v3/CommitProductSeo/{pid}",
                     json={**updates, "approvalToken": token})
        if val(commit, "Committed") is not True:
            raise RuntimeError("API did not confirm commit")
        record("COMMIT product succeeded", {"id": pid, "slug": val(commit, "Slug")})

    current = api("GET", f"/v3/ProductSnapshot/{pid}")
    expected = {
        "Name": updates["name"], "Sku": updates["sku"],
        "ShortDescription": updates["shortDescription"],
        "FullDescription": updates["fullDescription"],
        "MetaTitle": updates["metaTitle"], "MetaDescription": updates["metaDescription"],
        "MetaKeywords": updates["metaKeywords"], "Slug": NEW_SLUG
    }
    bad = {k: {"expected": v[:80], "actual": str(val(current, k))[:80]}
           for k,v in expected.items() if val(current,k) != v}
    if bad:
        report["verification_errors"] = bad
        save()
        raise RuntimeError("POST-COMMIT product verification failed: " + str(list(bad)))
    record("POST-COMMIT product verification OK",
           {"id": pid, "name": val(current, "Name"), "sku": val(current, "Sku"),
            "slug": val(current, "Slug"), "metaTitle": val(current, "MetaTitle")})

    # Check picture metadata in same test: no media file mutation.
    pictures = val(current, "Pictures", [])
    if pictures:
        pic = pictures[0]
        picture_id = int(val(pic, "Id"))
        p_request = {
            "scope": "product", "pictureId": picture_id,
            "altAttribute": "TEST API 3.0 – zdjęcie oryginalnego produktu świeca pieńkowa",
            "titleAttribute": "Zdjęcie testowe – Papiernia SEO API 3.0",
            "reason": "Zatwierdzona próba zapisu ALT i Title bez podmiany pliku"
        }
        if (val(pic, "AltAttribute") != p_request["altAttribute"]
            or val(pic, "TitleAttribute") != p_request["titleAttribute"]):
            preview = api("POST", f"/v3/PreviewPictureMetadata/{pid}", json=p_request)
            token = val(preview, "ApprovalToken")
            if not token: raise RuntimeError("Picture preview missing token")
            result = api("PUT", f"/v3/CommitPictureMetadata/{pid}",
                         json={**p_request, "approvalToken": token})
            if val(result, "Committed") is not True: raise RuntimeError("Picture commit failed")
        check_pic = api("GET", f"/v3/ProductPictures/{pid}")
        p = next((p for p in val(check_pic, "Pictures", []) if int(val(p,"Id")) == picture_id), None)
        if p is None or val(p, "AltAttribute") != p_request["altAttribute"] or val(p, "TitleAttribute") != p_request["titleAttribute"]:
            raise RuntimeError("Picture ALT/Title verification failed")
        record("PICTURE ALT/Title verification OK", {"pictureId": picture_id,
             "alt": val(p, "AltAttribute"), "title": val(p, "TitleAttribute")})
    else:
        record("No product pictures – picture test skipped", None)
    report["status"] = "success"
    report["after"] = {"name": val(current, "Name"), "slug": val(current, "Slug"),
         "sku": val(current, "Sku"), "metaTitle": val(current, "MetaTitle"),
         "metaDescription": val(current, "MetaDescription")}
    save()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        save()
        print(str(exc), file=sys.stderr)
        raise
