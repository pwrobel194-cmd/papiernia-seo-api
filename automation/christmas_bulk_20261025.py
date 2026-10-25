#!/usr/bin/env python3
# Jednorazowe wdrozenie SEO klastra Boze Narodzenie 2026.
# Bez zmian Name/H1, URL, ShortDescription, cen, zdjec i obrazow w HTML.
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = "https://papiernia.net.pl"
API = ROOT + "/papiernia-seo-api/v1"
HUB = ROOT + "/upominki-swiateczne"
KEY = os.environ.get("PAPIERNIA_SEO_API_KEY")
if not KEY:
    raise RuntimeError("Missing PAPIERNIA_SEO_API_KEY (GitHub secret)")
CLIENT = requests.Session()
CLIENT.headers.update({"X-Papiernia-SEO-Key": KEY})
PLAN = json.loads(Path("automation/christmas_20261025_plan.json").read_text(encoding="utf-8"))
RUNID = "christmas-seo-20261025"
BACKUP_DIR = Path("backups/christmas-bulk-20261025")
REPORT_PATH = Path("reports/christmas-bulk-20261025-result.json")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

FOCUS_LEADS = {
    "upominek-swiateczny-dla-klientow",
    "oryginalny-prezent-dla-klientow-upominek-swiateczny",
    "upominki-firmowe-dla-klientow",
    "upominki-firmowe-na-swieta",
    "tani-upominek-dla-klientow-na-swieta",
    "upominki-firmowe-dla-pracownikow",
    "slodkie-upominki-dla-klientow-na-swieta",
    "prezenciki-dla-klientow-na-swieta-bozego-narodzenia",
}
P_TAG = '<p class="pn-seo-kontekst-20261025" style="text-align:center;line-height:1.6;">'
LINK_TAG = '<p class="pn-seo-hub-20261025" style="text-align:center;line-height:1.6;margin:14px 0;">'
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
HREF_HUB_RE = re.compile(r'href\s*=\s*[^>]*?/upominki-swiateczne', re.I)

report = {
    "createdUtc": datetime.now(timezone.utc).isoformat(),
    "targetCategory": HUB,
    "plannedProducts": len(PLAN["products"]),
    "scope": ["metaTitle", "metaDescription", "product-specific focus lead where appropriate", "internal link to parent category"],
    "unchanged": ["Name / H1", "SeName / URL", "ShortDescription", "price", "gallery", "existing image tags in HTML"],
    "results": [],
}

def persist():
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

def get(endpoint, params=None):
    r = CLIENT.get(API + "/" + endpoint, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def put(endpoint, payload, dry_run):
    r = CLIENT.put(API + "/" + endpoint,
        params={"dryRun": str(dry_run).lower()}, json=payload, timeout=50)
    r.raise_for_status()
    return r.json()

def as_lc(obj):
    return {k[0].lower() + k[1:]: v for k, v in obj.items()}

def has_hub_link(s):
    return bool(HREF_HUB_RE.search(s or ""))

def new_full_description(slug, focus, meta_desc, original):
    old = original or ""
    result = old
    lead_added = False
    link_added = False
    typo_corrected = False
    if slug in FOCUS_LEADS and "pn-seo-kontekst-20261025" not in result and old.strip():
        content = P_TAG + "<strong>" + html.escape(focus) + ".</strong> " + html.escape(meta_desc) + "</p>"
        # Zachowaj pierwszy naglowek i kazdy dotychczasowy element HTML.
        m = re.search(r"</h[1-6]\s*>", result, re.I)
        if m and m.start() < 1800:
            result = result[:m.end()] + "\n" + content + result[m.end():]
        else:
            result = content + "\n" + result
        lead_added = True
    if not has_hub_link(result) and "pn-seo-hub-20261025" not in result:
        para = (LINK_TAG +
            "Szukasz innych wariantów? Przejrzyj także "
            '<a href="' + HUB + '" title="Upominki świąteczne dla klientów z logo">'
            "upominki świąteczne dla klientów i firm</a> w Papierni.</p>")
        result = result.rstrip() + "\n" + para
        link_added = True
    if slug == "oplatek-swiateczny-z-personalizowana-etykieta-na-wigilie-firmowa":
        for old_string, new_string in [
            ("Wybierz liczbę lizaków", "Wybierz liczbę opłatków"),
            ("wybierz liczbę lizaków", "wybierz liczbę opłatków"),
        ]:
            if old_string in result:
                result = result.replace(old_string, new_string)
                typo_corrected = True
    if IMG_RE.findall(result) != IMG_RE.findall(old):
        raise RuntimeError("Image tag invariants violated")
    if len(result) > 100000:
        raise RuntimeError("Result HTML exceeds 100000 chars")
    return result, {"focusLeadAdded":lead_added, "categoryLinkAdded":link_added, "oplatekTypoFixed":typo_corrected}

def main():
    health = get("Health")
    if health.get("ok") is not True:
        raise RuntimeError("Plugin API health check failed")
    report["healthOk"] = True
    category = get("Resolve", {"url": HUB})
    if category.get("entity") != "Category" or category.get("slug") != "upominki-swiateczne":
        raise RuntimeError("Category resolution failed")
    report["categoryId"] = category.get("id")
    seen_ids = set()
    for n, item in enumerate(PLAN["products"], 1):
        slug = item["slug"]
        entry = {"index": n, "slug": slug, "url": ROOT+"/"+slug}
        try:
            meta_title = item["metaTitle"].strip()
            meta_desc = item["metaDescription"].strip()
            if not (25 <= len(meta_title) <= 70 and 80 <= len(meta_desc) <= 175):
                raise RuntimeError("Invalid title/description length")
            resolved = get("Resolve", {"url": entry["url"]})
            if resolved.get("entity") != "Product" or resolved.get("slug") != slug or not resolved.get("Published") or resolved.get("Deleted"):
                raise RuntimeError("Product not active or Resolve mismatch: " + repr(resolved))
            product_id = int(resolved["id"])
            if product_id in seen_ids:
                raise RuntimeError("Duplicate product ID")
            seen_ids.add(product_id)
            entry["id"] = product_id
            before = get("Product/" + str(product_id))
            if before.get("SeName") != slug or before.get("Name") != resolved.get("Name") or not before.get("Published") or before.get("Deleted"):
                raise RuntimeError("Product changed or identity mismatch before edit")
            (BACKUP_DIR / (slug + ".json")).write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
            old_html = before.get("FullDescription") or ""
            html_after, details = new_full_description(slug, item["focus"], meta_desc, old_html)
            entry.update(details)
            payload = {
                "MetaTitle": meta_title,
                "MetaDescription": meta_desc,
                "RequestId": RUNID + "-" + str(product_id),
                "Reason": "SEO Christmas cluster: distinctive product intent and internal link to /upominki-swiateczne; preserve short descriptions, pictures and URL.",
            }
            if html_after != old_html:
                payload["FullDescription"] = html_after
            diff = {
                "metaTitle": before.get("MetaTitle") != meta_title,
                "metaDescription": before.get("MetaDescription") != meta_desc,
                "fullDescription": html_after != old_html,
            }
            entry["changedFields"] = [k for k,v in diff.items() if v]
            entry["metaTitleBefore"] = before.get("MetaTitle")
            entry["metaTitleAfter"] = meta_title
            if not entry["changedFields"]:
                entry["status"] = "NO_CHANGE"
                report["results"].append(entry)
                persist()
                continue
            dry = put("UpdateProduct/" + str(product_id), payload, True)
            if dry.get("ok") is not True or dry.get("dryRun") is not True:
                raise RuntimeError("Dry-run rejected " + repr(dry))
            changed = put("UpdateProduct/" + str(product_id), payload, False)
            if changed.get("ok") is not True or changed.get("dryRun") is not False:
                raise RuntimeError("Real PUT rejected " + repr(changed))
            after = get("Product/" + str(product_id))
            immutable = ["Name", "SeName", "ShortDescription", "Published", "Deleted"]
            if any(before.get(k) != after.get(k) for k in immutable):
                raise RuntimeError("Read-back: immutable field mismatch")
            if after.get("MetaTitle") != meta_title or after.get("MetaDescription") != meta_desc:
                raise RuntimeError("Read-back: metadata did not persist")
            if payload.get("FullDescription", old_html) != (after.get("FullDescription") or ""):
                raise RuntimeError("Read-back: full description did not persist")
            if IMG_RE.findall(after.get("FullDescription") or "") != IMG_RE.findall(old_html):
                raise RuntimeError("Read-back: image tags were modified")
            entry["status"] = "APPLIED_VERIFIED"
        except Exception as exc:
            entry["status"] = "ERROR"
            entry["error"] = str(exc)
        report["results"].append(entry)
        persist()
        print(json.dumps({k:entry.get(k) for k in ["index","slug","id","status","changedFields","error"]},ensure_ascii=False), flush=True)
    report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
    report["summary"] = {
        status: sum(1 for x in report["results"] if x["status"] == status)
        for status in ("APPLIED_VERIFIED", "NO_CHANGE", "ERROR")
    }
    persist()
    print("CHRISTMAS_BULK_SUMMARY=" + json.dumps(report["summary"], ensure_ascii=False), flush=True)
    return 2 if report["summary"]["ERROR"] else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        persist()
