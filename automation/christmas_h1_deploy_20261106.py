#!/usr/bin/env python3
"""Owner-approved 2026-11-06 deployment of EXACTLY four product H1 names.

No slug, meta, HTML, pictures, price, stock, categories, publication changes.
Uses v3 PreviewProductSeo then CommitProductSeo with fresh signed token.
Preflight checks ALL targets before first commit; fail closed on any drift.
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://papiernia.net.pl"
API = BASE + "/papiernia-seo-api"
REPORT = Path("reports/christmas-h1-deploy-20261106.json")
BACKUP = Path("backups/christmas-h1-deploy-20261106")
KEY = os.getenv("PAPIERNIA_SEO_API_KEY", "")

TARGETS = [
    {
        "id": 4922, "slug": "upominki-firmowe-dla-klientow",
        "old": "Świeczka serce w pudełeczku z logo – upominek firmowy dla klientów",
        "new": "Nieszablonowy upominek dla kontrahentów – świeczka z logo",
    },
    {
        "id": 4924, "slug": "upominki-firmowe-na-swieta",
        "old": "Różowe pudełeczko ze świeczką – upominek firmowy na Święta",
        "new": "Mini prezent dla klientek salonu – świeczka z personalizacją",
    },
    {
        "id": 4925, "slug": "upominki-firmowe-dla-pracownikow",
        "old": "Pudełeczko z ciasteczkiem z wróżbą – prezent dla pracowników",
        "new": "Mini prezent dla pracowników na święta – ciasteczko z wróżbą",
    },
    {
        "id": 4946, "slug": "tani-upominek-dla-klientow-na-swieta",
        "old": "Tani upominek świąteczny dla klientów – ciasteczko z wróżbą",
        "new": "Tanie podziękowanie dla klientek na święta – ciasteczko z wróżbą",
    },
]
REASON = ("Zatwierdzona przez właściciela 06.11.2026 optymalizacja H1 "
          "4 produktów Święta; istniejące URL/slug i pozostałe pola bez zmian")
UNTOUCHED = ("Sku", "ShortDescription", "FullDescription", "MetaTitle",
             "MetaDescription", "MetaKeywords", "Slug", "Published", "Deleted",
             "CategoryIds", "Pictures")
PREVIEW_UNTOUCHED = ("Sku", "ShortDescription", "FullDescription", "MetaTitle",
                     "MetaDescription", "MetaKeywords", "SeName", "UpdatedOnUtc")

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def v(o, key, default=None):
    return o.get(key, o.get(key[:1].lower() + key[1:], default))

def safe_save(data):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def request(session, method, path, **kw):
    # Absolute allowlist - never write anything except these exact four products.
    if method == "GET":
        if path != "/v1/Health" and not re.fullmatch(r"/v3/ProductSnapshot/(4922|4924|4925|4946)", path):
            raise RuntimeError("Disallowed read endpoint")
    elif method in ("POST", "PUT"):
        action = "PreviewProductSeo" if method == "POST" else "CommitProductSeo"
        if not re.fullmatch(r"/v3/" + action + r"/(4922|4924|4925|4946)", path):
            raise RuntimeError("Disallowed write endpoint")
    else:
        raise RuntimeError("Disallowed HTTP method")
    response = session.request(method, API + path, timeout=45, **kw)
    if not response.ok:
        raise RuntimeError(f"{method} {path} returned HTTP {response.status_code}; stopped")
    return response.json()

def snapshot(session, item):
    raw = request(session, "GET", f"/v3/ProductSnapshot/{item['id']}")
    if v(raw, "Ok") is not True or int(v(raw, "Id", -1)) != item["id"]:
        raise RuntimeError("Unexpected product snapshot identity")
    if v(raw, "Slug") != item["slug"]:
        raise RuntimeError("URL/slug mismatch detected BEFORE edit: " + item["slug"])
    if v(raw, "Published") is not True or v(raw, "Deleted") is True:
        raise RuntimeError("Product publication/deletion mismatch: " + item["slug"])
    return raw

def ensure_preview(preview, original, item):
    if v(preview, "Ok") is not True or v(preview, "DryRun") is not True:
        raise RuntimeError("Preview not confirmed by API")
    before, after = v(preview, "Before", {}), v(preview, "After", {})
    if v(before, "Name") != item["old"] or v(after, "Name") != item["new"]:
        raise RuntimeError("Preview unexpected Name diff")
    for field in PREVIEW_UNTOUCHED:
        original_value = v(original, "Slug") if field == "SeName" else v(original, field)
        if v(before, field) != original_value:
            raise RuntimeError("Preview before-state drift: " + field)
        if v(after, field) != v(before, field):
            raise RuntimeError("Preview wants to change protected field: " + field)
    token = v(preview, "ApprovalToken")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Missing signed approval token")
    return token

def verify_unchanged(before, after, item):
    if v(after, "Name") != item["new"]:
        raise RuntimeError("Post-commit H1 mismatch")
    for field in UNTOUCHED:
        if v(before, field) != v(after, field):
            raise RuntimeError("Post-commit protected field changed: " + field)
    if v(after, "Slug") != item["slug"]:
        raise RuntimeError("Post-commit slug changed unexpectedly")

def public_check(session, item):
    # No redirects are allowed at the existing canonical product URL.
    url = BASE + "/" + item["slug"]
    resp = requests.get(url, timeout=35, allow_redirects=False, headers={"User-Agent": "Papiernia-SEO-Verification/1.0"})
    result = {"url": url, "status": resp.status_code, "location": resp.headers.get("Location")}
    if resp.status_code != 200:
        result["warning"] = "Original URL not HTTP 200; check storefront / caching"
        return result
    match = re.search(r"<h1\b[^>]*>(.*?)</h1>", resp.text, flags=re.I | re.S)
    if match:
        result["h1"] = html.unescape(re.sub(r"<[^>]*>", "", match.group(1))).strip()
        if result["h1"] != item["new"]:
            result["warning"] = "Public H1 differs (possible cache); API read-back is authoritative"
    else:
        result["warning"] = "Unable to locate public H1 in HTML response"
    return result

def main():
    report = {
        "dateUtc": utc_now(),
        "authorization": "Właściciel zatwierdził 4 opisane H1 w rozmowie 2026-11-06: OK działamy",
        "scope": "EXACTLY FOUR PRODUCT NAMES (H1) ONLY",
        "protected": ["SeName / URL", "short/full HTML", "images/ALT", "SKU", "meta fields",
                      "price", "inventory", "status", "category and layout"],
        "status": "STARTED",
        "products": [],
    }
    safe_save(report)
    if not KEY:
        raise RuntimeError("Missing GitHub Actions API secret; no live requests")
    if len(TARGETS) != 4 or len({t["id"] for t in TARGETS}) != 4:
        raise RuntimeError("Invalid allowlist")
    session = requests.Session()
    session.headers.update({"X-Papiernia-SEO-Key": KEY, "Accept": "application/json"})

    health = request(session, "GET", "/v1/Health")
    if v(health, "Ok") is not True:
        raise RuntimeError("API health failed")

    # 1) Complete PRE-FLIGHT before any mutation, with complete backups.
    backups, todo = {}, []
    for item in TARGETS:
        raw = snapshot(session, item)
        current = v(raw, "Name")
        if current not in (item["old"], item["new"]):
            raise RuntimeError(f"Existing H1 differs from approved original: {item['slug']}")
        backups[item["id"]] = raw
        BACKUP.mkdir(parents=True, exist_ok=True)
        (BACKUP / f"{item['id']}-before.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        entry = {
            "id": item["id"], "slug": item["slug"],
            "beforeName": current, "requestedName": item["new"],
            "slugBefore": v(raw, "Slug"),
            "status": "ALREADY_APPLIED" if current == item["new"] else "PREFLIGHT_OK",
        }
        report["products"].append(entry)
        if current != item["new"]:
            todo.append(item)
        safe_save(report)

    # 2) Previews for ALL pending edits, no writes yet.
    tokens = {}
    for item in todo:
        payload = {"name": item["new"], "reason": REASON}
        pv = request(session, "POST",
                     f"/v3/PreviewProductSeo/{item['id']}", json=payload)
        tokens[item["id"]] = ensure_preview(pv, backups[item["id"]], item)
        next(p for p in report["products"] if p["id"] == item["id"])["status"] = "PREVIEW_VERIFIED"
        safe_save(report)
    # Verify the source did not mutate while preparing previews.
    for item in TARGETS:
        if snapshot(session, item) != backups[item["id"]]:
            raise RuntimeError(f"Product changed while previewing: {item['slug']}")
    report["status"] = "ALL_PREFLIGHTS_PASSED"
    safe_save(report)

    # 3) Commit with fresh, signed, time-limited token. Stop on first error.
    for item in todo:
        entry = next(p for p in report["products"] if p["id"] == item["id"])
        entry["status"] = "COMMIT_REQUESTED"
        safe_save(report)
        payload = {"name": item["new"], "reason": REASON,
                   "approvalToken": tokens[item["id"]]}
        answer = request(session, "PUT",
                         f"/v3/CommitProductSeo/{item['id']}", json=payload)
        if v(answer, "Committed") is not True or v(answer, "Slug") != item["slug"]:
            raise RuntimeError("Commit not confirmed or response slug changed: " + item["slug"])
        entry["status"] = "COMMIT_CONFIRMED"
        safe_save(report)
        result = snapshot(session, item)
        verify_unchanged(backups[item["id"]], result, item)
        (BACKUP / f"{item['id']}-after.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        entry["afterName"] = v(result, "Name")
        entry["slugAfter"] = v(result, "Slug")
        entry["status"] = "APPLIED_VERIFIED"
        try:
            entry["public"] = public_check(session, item)
        except requests.RequestException:
            entry["public"] = {"warning": "Public storefront request timed out; API readback passed"}
        safe_save(report)
        print(json.dumps({"id": item["id"], "slug": item["slug"],
                          "status": entry["status"], "slugUnchanged": True},
                          ensure_ascii=False), flush=True)

    report["summary"] = {
        "planned": 4,
        "appliedVerified": sum(p["status"] == "APPLIED_VERIFIED" for p in report["products"]),
        "alreadyApplied": sum(p["status"] == "ALREADY_APPLIED" for p in report["products"]),
        "errors": 0,
    }
    report["status"] = "SUCCESS"
    report["finishedUtc"] = utc_now()
    safe_save(report)
    print("SUMMARY " + json.dumps(report["summary"]), flush=True)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        if REPORT.exists():
            d = json.loads(REPORT.read_text(encoding="utf-8"))
        else:
            d = {"products": []}
        d["status"] = "ERROR_STOPPED"
        d["error"] = str(exc)
        d["finishedUtc"] = utc_now()
        safe_save(d)
        print("ERROR_STOPPED " + str(exc), file=sys.stderr, flush=True)
        sys.exit(1)
