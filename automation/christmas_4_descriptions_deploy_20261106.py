#!/usr/bin/env python3
"""Write only four explicitly approved FullDescription updates.

The approved changes come from the 2026-11-06 HTML proposal ZIP.
Exact SHA-256 of original and target HTML is mandatory; all original
<img> and <a> tags preserved byte-for-byte, order preserved.
URL/slug, H1, meta, short description, pictures, SKU, status untouched.
"""
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
import requests

BASE = "https://papiernia.net.pl"
API = BASE + "/papiernia-seo-api"
PLAN = Path("automation/christmas_4_descriptions_20261106.json")
REPORT = Path("reports/christmas-4-descriptions-deploy-20261106.json")
BACKUP = Path("backups/christmas-4-descriptions-20261106")
API_KEY = os.getenv("PAPIERNIA_SEO_API_KEY", "")
ANCHOR = '<p style="text-align: center; margin-top: 28px;">'
REASON = ("Właściciel zatwierdził 06.11.2026 dokładne rozszerzenia "
          "pełnych opisów 4 świątecznych produktów. Zachowano wszystkie "
          "zdjęcia HTML, URL i pozostałe pola.")
IMMUTABLE_SNAPSHOT_FIELDS = (
    "Id", "Name", "Sku", "ShortDescription", "MetaTitle",
    "MetaDescription", "MetaKeywords", "Slug", "Published",
    "Deleted", "CategoryIds", "Pictures",
)
IMMUTABLE_PREVIEW_FIELDS = (
    "Name", "Sku", "ShortDescription", "MetaTitle",
    "MetaDescription", "MetaKeywords", "SeName", "UpdatedOnUtc",
)
IDS = {4922, 4924, 4925, 4946}

def now():
    return datetime.now(timezone.utc).isoformat()

def value(o, name, default=None):
    return o.get(name, o.get(name[:1].lower() + name[1:], default))

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def tags(s, kind):
    return re.findall(r"<" + kind + r"\b[^>]*>", s or "", flags=re.I)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def api(client, method, endpoint, **kwargs):
    if method == "GET":
        if endpoint != "/v1/Health" and not re.fullmatch(
                r"/v3/ProductSnapshot/(?:4922|4924|4925|4946)", endpoint):
            raise RuntimeError("Unauthorized read endpoint: " + endpoint)
    elif method in ("POST", "PUT"):
        action = "PreviewProductSeo" if method == "POST" else "CommitProductSeo"
        if not re.fullmatch(
                r"/v3/" + action + r"/(?:4922|4924|4925|4946)", endpoint):
            raise RuntimeError("Unauthorized change endpoint: " + endpoint)
    else:
        raise RuntimeError("Unauthorized method")
    response = client.request(method, API + endpoint, timeout=45, **kwargs)
    if not response.ok:
        raise RuntimeError(method + " " + endpoint +
                           " rejected (HTTP " + str(response.status_code) + ")")
    result = response.json()
    if value(result, "Ok") is not True:
        raise RuntimeError("API did not report OK: " + endpoint)
    return result

def snapshot(client, target):
    x = api(client, "GET", "/v3/ProductSnapshot/" + str(target["id"]))
    if value(x, "Id") != target["id"] or value(x, "Slug") != target["slug"]:
        raise RuntimeError("ID or SLUG mismatch: " + target["slug"])
    if value(x, "Name") != target["name"]:
        raise RuntimeError("Previously approved H1 differs: " + target["slug"])
    if value(x, "Published") is not True or value(x, "Deleted") is True:
        raise RuntimeError("Product is not active: " + target["slug"])
    return x

def build_html(original, target):
    result = original
    for old,new in ((target["old_h2"],target["new_h2"]),
                    (target["second_old_h2"],target["second_new_h2"])):
        old_tag = ">" + old + "</h2>"
        new_tag = ">" + new + "</h2>"
        if result.count(old_tag) != 1:
            raise RuntimeError("Expected unique existing H2 missing: " + target["slug"])
        result = result.replace(old_tag,new_tag,1)
    if result.count(ANCHOR) != 1:
        raise RuntimeError("Expected unique append point absent: " + target["slug"])
    paragraphs = "\r\n".join(
        '<p style="text-align: center;">' + html.escape(p) + "</p>"
        for p in target["paras"]
    )
    result = result.replace(ANCHOR, paragraphs + "\r\n" + ANCHOR, 1)
    return result

def invariant(original, proposed, target):
    if sha(original) != target["old_sha"] and sha(original) != target["new_sha"]:
        raise RuntimeError("Live description differs from approved proposal source: " +
                           target["slug"])
    if sha(proposed) != target["new_sha"]:
        raise RuntimeError("Generated HTML does not exactly match APPROVED ZIP SHA-256: " +
                           target["slug"])
    for kind,expected in (("img",target["img"]),("a",target["links"])):
        t1,t2 = tags(original,kind),tags(proposed,kind)
        if t1 != t2 or len(t1) != expected:
            raise RuntimeError("Original " + kind +
                               " elements changed, removed or reordered: " +
                               target["slug"])
    if original.count("/upominki-swiateczne") != proposed.count("/upominki-swiateczne"):
        raise RuntimeError("Category internal link count changed")
    if original.count("do samodziel") > proposed.count("do samodziel"):
        raise RuntimeError("Assembly notices lost")
    if len(proposed) < len(original):
        raise RuntimeError("Original description shortened")
    return True

def ensure_preview(preview, before, new_html, target):
    if value(preview,"DryRun") is not True:
        raise RuntimeError("API preview did not report dry run")
    b, a = value(preview, "Before", {}), value(preview, "After", {})
    if value(b,"FullDescription") != value(before,"FullDescription"):
        raise RuntimeError("Preview source HTML changed unexpectedly")
    if value(a,"FullDescription") != new_html:
        raise RuntimeError("Preview target HTML differs from approved exact HTML")
    for key in IMMUTABLE_PREVIEW_FIELDS:
        expected = value(before,"Slug") if key == "SeName" else value(before,key)
        if value(b,key) != expected or value(a,key) != expected:
            raise RuntimeError("Preview wants to change protected field: " + key)
    token = value(preview, "ApprovalToken")
    if not isinstance(token,str) or len(token) < 30:
        raise RuntimeError("Signed approval token missing")
    return token

def after_check(before, after, target, expected_html):
    if value(after, "FullDescription") != expected_html:
        raise RuntimeError("FullDescription did not persist exactly")
    if sha(value(after, "FullDescription")) != target["new_sha"]:
        raise RuntimeError("FullDescription hash after commit mismatch")
    for field in IMMUTABLE_SNAPSHOT_FIELDS:
        if value(before,field) != value(after,field):
            raise RuntimeError("Protected field changed: " + field)
    if tags(value(before,"FullDescription"),"img") != tags(value(after,"FullDescription"),"img"):
        raise RuntimeError("Images changed in stored HTML")
    if tags(value(before,"FullDescription"),"a") != tags(value(after,"FullDescription"),"a"):
        raise RuntimeError("Links changed in stored HTML")

def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    targets = plan["products"]
    if len(targets) != 4 or {t["id"] for t in targets} != IDS or len({t["slug"] for t in targets}) != 4:
        raise RuntimeError("Unsafe edit scope")
    if not API_KEY:
        raise RuntimeError("No API secret available")
    client = requests.Session()
    client.headers.update({"X-Papiernia-SEO-Key": API_KEY, "Accept": "application/json"})
    if value(api(client,"GET","/v1/Health"),"Ok") is not True:
        raise RuntimeError("Unhealthy API")
    report = {"status":"PREFLIGHT", "startedUtc":now(),
              "scope":"FullDescription only on exactly four products",
              "source":"Approved ZIP generated 2026-11-06, exact SHA-256 enforced",
              "protect":"all original img and a tags verbatim, URL/slug, H1, meta, short description, pictures, categories, SKU and status",
              "products":[]}
    write_json(REPORT,report)
    before, desired, pending, tokens = {}, {}, [], {}
    # All four original snapshots MUST be checked before ANY commit.
    for t in targets:
        id = t["id"]
        original = snapshot(client,t)
        before[id] = original
        html_before = value(original,"FullDescription") or ""
        current_sha = sha(html_before)
        if current_sha == t["new_sha"]:
            result_html = html_before
            state = "ALREADY_APPLIED"
        elif current_sha == t["old_sha"]:
            result_html = build_html(html_before,t)
            state = "READY"
            pending.append(t)
        else:
            raise RuntimeError("Unexpected live HTML hash: " + t["slug"])
        # For already applied, compare imagery to original stored snapshot? If new hash,
        # the exact full approved HTML hash itself guards all image elements.
        if current_sha == t["old_sha"]:
            invariant(html_before, result_html, t)
        if sha(result_html) != t["new_sha"]:
            raise RuntimeError("Unexpected target HTML hash: " + t["slug"])
        desired[id] = result_html
        BACKUP.mkdir(parents=True,exist_ok=True)
        write_json(BACKUP / (str(id)+"-before.json"),original)
        report["products"].append({
            "id":id,"url":BASE + "/" + t["slug"],"slug":t["slug"],
            "status":state,"name":t["name"],
            "beforeSha256":current_sha,"targetSha256":t["new_sha"],
            "images":t["img"],"links":t["links"],
        })
        write_json(REPORT,report)
    # Preview ALL pending updates, validate exact field-level diffs.
    for t in pending:
        id=t["id"]
        preview=api(client,"POST",f"/v3/PreviewProductSeo/{id}",
                    json={"fullDescription":desired[id],"reason":REASON})
        tokens[id] = ensure_preview(preview,before[id],desired[id],t)
        item=next(x for x in report["products"] if x["id"]==id)
        item["status"]="PREVIEW_OK"
        write_json(REPORT,report)
    # Reject concurrent changes before first production write.
    for t in targets:
        if snapshot(client,t) != before[t["id"]]:
            raise RuntimeError("Live product changed during preflight: " + t["slug"])
    report["status"]="PREFLIGHT_ALL_FOUR_PASSED"
    write_json(REPORT,report)
    # Commit only the exact approved FullDescription field, no name or slug sent.
    for t in pending:
        id=t["id"]
        item=next(x for x in report["products"] if x["id"]==id)
        item["status"]="COMMIT_SENT"
        write_json(REPORT,report)
        result=api(client,"PUT",f"/v3/CommitProductSeo/{id}",json={
            "fullDescription":desired[id],
            "approvalToken":tokens[id],
            "reason":REASON,
        })
        if value(result,"Committed") is not True or value(result,"Slug")!=t["slug"]:
            raise RuntimeError("API failed to confirm commit with unchanged slug: " + t["slug"])
        item["status"]="COMMIT_CONFIRMED"
        write_json(REPORT,report)
        updated=snapshot(client,t)
        after_check(before[id],updated,t,desired[id])
        write_json(BACKUP / (str(id)+"-after.json"),updated)
        item["afterSha256"]=sha(value(updated,"FullDescription"))
        item["slugAfter"]=value(updated,"Slug")
        item["status"]="APPLIED_VERIFIED"
        write_json(REPORT,report)
        print(json.dumps({"id":id,"status":item["status"],
            "imagesPreserved":t["img"],"slugUnchanged":True},ensure_ascii=False),flush=True)
    report["status"]="SUCCESS"
    report["finishedUtc"]=now()
    report["summary"]={
        "total":4,
        "appliedVerified":sum(x["status"]=="APPLIED_VERIFIED" for x in report["products"]),
        "alreadyApplied":sum(x["status"]=="ALREADY_APPLIED" for x in report["products"]),
        "errors":0,
        "imagesPreservedTotal":sum(t["img"] for t in targets),
    }
    write_json(REPORT,report)
    print("FINAL_SUMMARY "+json.dumps(report["summary"],ensure_ascii=False),flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        data=json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
        data["status"]="STOPPED_ERROR"
        data["error"]=str(error)
        data["finishedUtc"]=now()
        write_json(REPORT,data)
        print("STOPPED_ERROR: "+str(error),file=sys.stderr,flush=True)
        sys.exit(1)
