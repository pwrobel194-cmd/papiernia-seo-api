import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from openai import OpenAI

BASE_URL = "https://papiernia.net.pl"
API_BASE = f"{BASE_URL}/papiernia-seo-api/v1"
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

AUTO_APPLY_SAFE = os.getenv("AUTO_APPLY_SAFE", "false").lower() == "true"
MAX_CHANGES = int(os.getenv("MAX_CHANGES", "3"))
MIN_IMPRESSIONS = int(os.getenv("MIN_IMPRESSIONS", "50"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

SEO_KEY = os.environ.get("PAPIERNIA_SEO_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GSC_SERVICE_ACCOUNT_JSON = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "")

if not SEO_KEY or not OPENAI_API_KEY or not GSC_SERVICE_ACCOUNT_JSON:
    raise RuntimeError("Missing required GitHub Actions secrets")

HEADERS = {"X-Papiernia-SEO-Key": SEO_KEY}
client = OpenAI(api_key=OPENAI_API_KEY)


def gsc_session():
    info = json.loads(GSC_SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(info, scopes=[GSC_SCOPE])
    return AuthorizedSession(creds)


def detect_gsc_property(session):
    response = session.get("https://www.googleapis.com/webmasters/v3/sites", timeout=30)
    response.raise_for_status()
    entries = response.json().get("siteEntry", [])
    candidates = [x["siteUrl"] for x in entries if "papiernia.net.pl" in x.get("siteUrl", "")]
    if not candidates:
        raise RuntimeError("Service account has no Search Console access to papiernia.net.pl")
    domain = [x for x in candidates if x == "sc-domain:papiernia.net.pl"]
    return domain[0] if domain else sorted(candidates, key=len)[0]


def query_gsc(session, site_url, start_date, end_date):
    url = "https://www.googleapis.com/webmasters/v3/sites/" + quote(site_url, safe="") + "/searchAnalytics/query"
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["page", "query"],
        "rowLimit": 25000,
        "dataState": "final",
        "type": "web",
    }
    response = session.post(url, json=body, timeout=90)
    response.raise_for_status()
    return response.json().get("rows", [])


def page_metrics(rows):
    pages = defaultdict(lambda: {
        "clicks": 0.0,
        "impressions": 0.0,
        "position_numerator": 0.0,
        "queries": defaultdict(lambda: {"clicks": 0.0, "impressions": 0.0, "position_numerator": 0.0}),
    })
    query_pages = defaultdict(lambda: defaultdict(float))

    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        page, query = keys[0], keys[1]
        clicks = float(row.get("clicks", 0))
        impressions = float(row.get("impressions", 0))
        position = float(row.get("position", 0))

        p = pages[page]
        p["clicks"] += clicks
        p["impressions"] += impressions
        p["position_numerator"] += position * impressions

        q = p["queries"][query]
        q["clicks"] += clicks
        q["impressions"] += impressions
        q["position_numerator"] += position * impressions

        query_pages[query][page] += impressions

    result = {}
    for page, p in pages.items():
        imp = p["impressions"]
        queries = []
        for qtext, q in p["queries"].items():
            qimp = q["impressions"]
            queries.append({
                "query": qtext,
                "clicks": round(q["clicks"], 2),
                "impressions": round(qimp, 2),
                "ctr": round(q["clicks"] / qimp, 4) if qimp else 0,
                "position": round(q["position_numerator"] / qimp, 2) if qimp else 0,
            })
        queries.sort(key=lambda x: x["impressions"], reverse=True)
        result[page] = {
            "clicks": round(p["clicks"], 2),
            "impressions": round(imp, 2),
            "ctr": round(p["clicks"] / imp, 4) if imp else 0,
            "position": round(p["position_numerator"] / imp, 2) if imp else 0,
            "top_queries": queries[:12],
        }

    cannibal = {
        query: sorted(page_map.items(), key=lambda x: x[1], reverse=True)
        for query, page_map in query_pages.items()
        if len(page_map) >= 2 and sum(page_map.values()) >= 30
    }
    return result, cannibal


def is_candidate_url(url):
    bad = (
        "/admin", "/login", "/register", "/cart", "/checkout", "/search",
        "/wishlist", "/compareproducts", "/customer", "/order",
    )
    lower = url.lower()
    return lower.startswith(BASE_URL) and not any(x in lower for x in bad)


def score_candidates(current, previous, cannibal):
    items = []
    for page, cur in current.items():
        if not is_candidate_url(page) or cur["impressions"] < MIN_IMPRESSIONS:
            continue

        prev = previous.get(page, {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0})
        position = cur["position"]
        score = 0.0
        reasons = []

        if 4 <= position <= 10:
            score += 40
            reasons.append("pozycja 4-10")
        elif 10 < position <= 20:
            score += 35
            reasons.append("pozycja 11-20")

        score += min(25, cur["impressions"] / 200)

        if position <= 10 and cur["ctr"] < 0.02 and cur["impressions"] >= 100:
            score += 20
            reasons.append("niski CTR")
        elif 10 < position <= 20 and cur["ctr"] < 0.01 and cur["impressions"] >= 100:
            score += 15
            reasons.append("niski CTR")

        if prev.get("clicks", 0) >= 5:
            drop = (prev["clicks"] - cur["clicks"]) / prev["clicks"]
            if drop >= 0.30:
                score += 20
                reasons.append(f"spadek kliknięć {drop:.0%}")

        page_queries = {x["query"] for x in cur["top_queries"][:8]}
        cannibal_queries = [q for q in page_queries if q in cannibal]
        if cannibal_queries:
            score += min(15, len(cannibal_queries) * 5)
            reasons.append("możliwa kanibalizacja")

        if score >= 35:
            items.append({
                "page": page,
                "score": round(score, 1),
                "reasons": reasons,
                "current": cur,
                "previous": prev,
                "cannibal_queries": cannibal_queries[:5],
            })

    items.sort(key=lambda x: x["score"], reverse=True)
    return items


def api_get(path, params=None):
    r = requests.get(f"{API_BASE}/{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def api_put(path, payload, dry_run=True):
    r = requests.put(
        f"{API_BASE}/{path}",
        headers={**HEADERS, "Content-Type": "application/json"},
        params={"dryRun": "true" if dry_run else "false"},
        json=payload,
        timeout=45,
    )
    r.raise_for_status()
    return r.json()


def parse_json_object(text):
    text = text.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        text = re.sub(r"^.{3}(?:json)?\s*", "", text)
        text = re.sub(r"\s*.{3}$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def propose(entity, metrics):
    existing = {
        "name": entity.get("name") or entity.get("Name"),
        "metaTitle": entity.get("metaTitle") or entity.get("MetaTitle"),
        "metaDescription": entity.get("metaDescription") or entity.get("MetaDescription"),
        "shortDescription": entity.get("shortDescription") or entity.get("ShortDescription"),
        "description": entity.get("description") or entity.get("Description"),
        "fullDescription": entity.get("fullDescription") or entity.get("FullDescription"),
    }

    prompt = f"""
Jesteś ostrożnym specjalistą SEO e-commerce dla papiernia.net.pl.
Masz zoptymalizować WYŁĄCZNIE Meta Title i Meta Description istniejącej strony.

Zasady:
- Nie zmieniaj URL, nazwy produktu/kategorii ani treści strony.
- Nie wymyślaj faktów, cen, terminów, opinii ani cech, których nie ma w danych.
- Nie upychaj słów kluczowych.
- Title: najlepiej 35-65 znaków.
- Meta Description: najlepiej 100-165 znaków.
- Zachowaj naturalny język polski.
- Jeśli aktualne meta są już dobre i zmiana nie ma wyraźnego uzasadnienia, ustaw change=false.
- Priorytetem są frazy z realnymi wyświetleniami w Search Console.
- Nie obiecuj wzrostu pozycji ani CTR.

DANE STRONY:
{json.dumps(existing, ensure_ascii=False)[:16000]}

DANE GSC:
{json.dumps(metrics, ensure_ascii=False)[:12000]}

Zwróć TYLKO JSON:
{{
  "change": true,
  "metaTitle": "...",
  "metaDescription": "...",
  "reason": "krótkie uzasadnienie na podstawie GSC",
  "confidence": 0.0,
  "risk": "low"
}}
confidence ma być od 0 do 1. risk może być: low, medium, high.
"""
    response = client.responses.create(model=OPENAI_MODEL, input=prompt)
    return parse_json_object(response.output_text)


def validate(proposal):
    if not proposal.get("change"):
        return False, "model_no_change"
    title = (proposal.get("metaTitle") or "").strip()
    desc = (proposal.get("metaDescription") or "").strip()
    confidence = float(proposal.get("confidence", 0))
    risk = proposal.get("risk", "").lower()

    if not 25 <= len(title) <= 70:
        return False, f"title_length_{len(title)}"
    if not 80 <= len(desc) <= 175:
        return False, f"description_length_{len(desc)}"
    if confidence < 0.90:
        return False, "confidence_below_0.90"
    if risk != "low":
        return False, f"risk_{risk or 'missing'}"
    return True, "ok"


def updated_recently(entity, days=21):
    value = entity.get("updatedOnUtc") or entity.get("UpdatedOnUtc")
    if not value:
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - dt < timedelta(days=days)
    except Exception:
        return True


def main():
    health = api_get("Health")
    if not health.get("ok"):
        raise RuntimeError("Papiernia SEO API health check failed")

    session = gsc_session()
    site_url = detect_gsc_property(session)

    end_current = date.today() - timedelta(days=3)
    start_current = end_current - timedelta(days=27)
    end_previous = start_current - timedelta(days=1)
    start_previous = end_previous - timedelta(days=27)

    current_rows = query_gsc(session, site_url, start_current, end_current)
    previous_rows = query_gsc(session, site_url, start_previous, end_previous)

    current, cannibal = page_metrics(current_rows)
    previous, _ = page_metrics(previous_rows)
    candidates = score_candidates(current, previous, cannibal)

    report = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "gscProperty": site_url,
        "currentPeriod": [start_current.isoformat(), end_current.isoformat()],
        "previousPeriod": [start_previous.isoformat(), end_previous.isoformat()],
        "autoApplySafe": AUTO_APPLY_SAFE,
        "candidatesFound": len(candidates),
        "processed": [],
    }

    accepted = 0
    for candidate in candidates[:12]:
        if accepted >= MAX_CHANGES:
            break

        page = candidate["page"]
        try:
            resolved = api_get("Resolve", {"url": page})
            entity_type = resolved.get("entity")
            entity_id = resolved.get("id")
            if entity_type not in ("Product", "Category") or not entity_id:
                continue

            entity = api_get(f"{entity_type}/{entity_id}")
            published = entity.get("published")
            if published is None:
                published = entity.get("Published", True)
            deleted = entity.get("deleted")
            if deleted is None:
                deleted = entity.get("Deleted", False)
            if deleted or not published:
                continue

            if updated_recently(entity, 21):
                report["processed"].append({
                    "page": page,
                    "status": "skipped_recently_updated",
                    "score": candidate["score"],
                })
                continue

            proposal = propose(entity, candidate)
            valid, validation = validate(proposal)

            old_title = (entity.get("metaTitle") or entity.get("MetaTitle") or "").strip()
            old_desc = (entity.get("metaDescription") or entity.get("MetaDescription") or "").strip()

            if proposal.get("metaTitle", "").strip() == old_title and proposal.get("metaDescription", "").strip() == old_desc:
                valid = False
                validation = "no_effective_change"

            record = {
                "page": page,
                "entity": entity_type,
                "id": entity_id,
                "score": candidate["score"],
                "reasons": candidate["reasons"],
                "proposal": proposal,
                "validation": validation,
            }

            if not valid:
                record["status"] = "proposal_rejected"
                report["processed"].append(record)
                continue

            payload = {
                "metaTitle": proposal["metaTitle"].strip(),
                "metaDescription": proposal["metaDescription"].strip(),
                "requestId": f"seo-{date.today().isoformat()}-{entity_type.lower()}-{entity_id}",
                "reason": proposal.get("reason", "SEO opportunity from GSC"),
            }

            dry_run = not AUTO_APPLY_SAFE
            result = api_put(f"Update{entity_type}/{entity_id}", payload, dry_run=dry_run)
            record["status"] = "dry_run" if dry_run else "applied"
            record["apiResult"] = result
            report["processed"].append(record)
            accepted += 1

        except Exception as exc:
            report["processed"].append({
                "page": page,
                "status": "error",
                "error": str(exc),
            })

    Path("reports").mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    json_path = Path("reports") / f"seo-run-{stamp}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# Papiernia SEO Autopilot",
        "",
        f"- GSC: {site_url}",
        f"- okres: {start_current} – {end_current}",
        f"- kandydatów: {len(candidates)}",
        f"- tryb: {'AUTO APPLY' if AUTO_APPLY_SAFE else 'DRY RUN'}",
        "",
        "## Wyniki",
    ]
    for item in report["processed"]:
        md.append(f"- **{item.get('status')}** — {item.get('page')} — score {item.get('score', '-')}")
        if item.get("proposal"):
            md.append(f"  - Title: {item['proposal'].get('metaTitle', '')}")
            md.append(f"  - Description: {item['proposal'].get('metaDescription', '')}")
            md.append(f"  - Powód: {item['proposal'].get('reason', '')}")
    md_path = Path("reports") / f"seo-run-{stamp}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({
        "gscProperty": site_url,
        "candidates": len(candidates),
        "processed": len(report["processed"]),
        "mode": "apply" if AUTO_APPLY_SAFE else "dry-run",
        "report": str(json_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        raise
