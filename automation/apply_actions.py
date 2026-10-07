import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://papiernia.net.pl"
API_BASE = f"{BASE_URL}/papiernia-seo-api/v1"
SEO_KEY = os.environ.get("PAPIERNIA_SEO_API_KEY", "")
AUTO_APPLY = os.getenv("AUTO_APPLY_SAFE", "false").lower() == "true"

if not SEO_KEY:
    raise RuntimeError("Missing PAPIERNIA_SEO_API_KEY")

HEADERS = {"X-Papiernia-SEO-Key": SEO_KEY}

COMMON_FIELDS = {"url", "metaTitle", "metaDescription", "metaKeywords", "reason"}
CATEGORY_FIELDS = COMMON_FIELDS | {"description"}
PRODUCT_FIELDS = COMMON_FIELDS | {"shortDescription", "fullDescription"}


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


def validate_common(action):
    if not action.get("url", "").startswith(BASE_URL + "/"):
        raise ValueError("URL outside papiernia.net.pl")

    if "metaTitle" in action:
        title = (action.get("metaTitle") or "").strip()
        if not 25 <= len(title) <= 70:
            raise ValueError(f"Title length {len(title)} outside safe range 25-70")

    if "metaDescription" in action:
        desc = (action.get("metaDescription") or "").strip()
        if not 80 <= len(desc) <= 175:
            raise ValueError(f"Meta description length {len(desc)} outside safe range 80-175")

    if "metaKeywords" in action and len(action.get("metaKeywords") or "") > 500:
        raise ValueError("Meta keywords too long")

    for field in ("description", "shortDescription", "fullDescription"):
        if field in action and len(action.get(field) or "") > 30000:
            raise ValueError(f"{field} too long")

    editable = {"metaTitle", "metaDescription", "metaKeywords", "description", "shortDescription", "fullDescription"}
    if not any(field in action for field in editable):
        raise ValueError("Action contains no editable SEO fields")


def validate_for_entity(action, entity):
    validate_common(action)
    allowed = CATEGORY_FIELDS if entity == "Category" else PRODUCT_FIELDS
    unknown = set(action) - allowed
    if unknown:
        raise ValueError(f"Unsupported fields for {entity}: {sorted(unknown)}")


def read_current(entity, current):
    def get(name):
        value = current.get(name)
        if value is None:
            value = current.get(name[0].upper() + name[1:])
        return value

    data = {
        "metaTitle": get("metaTitle"),
        "metaDescription": get("metaDescription"),
        "metaKeywords": get("metaKeywords"),
    }
    if entity == "Category":
        data["description"] = get("description")
    else:
        data["shortDescription"] = get("shortDescription")
        data["fullDescription"] = get("fullDescription")
    return data


def build_payload(action, entity, entity_id):
    editable = ["metaTitle", "metaDescription", "metaKeywords"]
    editable += ["description"] if entity == "Category" else ["shortDescription", "fullDescription"]

    payload = {
        field: action[field].strip() if isinstance(action[field], str) else action[field]
        for field in editable
        if field in action
    }
    payload["requestId"] = (
        f"chatgpt-seo-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        f"-{entity.lower()}-{entity_id}"
    )
    payload["reason"] = action.get("reason", "ChatGPT SEO automation")
    return payload


def main():
    source = json.loads(Path("automation/actions.json").read_text(encoding="utf-8"))
    actions = source.get("actions", [])
    if not 1 <= len(actions) <= 5:
        raise RuntimeError("Safe run requires 1-5 actions")

    health = api_get("Health")
    report = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "pluginHealth": health,
        "mode": "APPLY" if AUTO_APPLY else "DRY_RUN",
        "results": [],
    }

    for action in actions:
        record = {"url": action.get("url")}
        try:
            resolved = api_get("Resolve", {"url": action["url"]})
            entity = resolved.get("entity")
            entity_id = resolved.get("id")
            if entity not in ("Product", "Category") or not entity_id:
                raise RuntimeError(f"Unsupported entity: {resolved}")

            validate_for_entity(action, entity)

            current = api_get(f"{entity}/{entity_id}")
            record["entity"] = entity
            record["id"] = entity_id

            before_all = read_current(entity, current)
            payload = build_payload(action, entity, entity_id)
            edit_fields = [k for k in payload if k not in ("requestId", "reason")]
            before = {field: before_all.get(field) for field in edit_fields}
            after = {field: payload[field] for field in edit_fields}
            record["before"] = before
            record["after"] = after

            if before == after:
                record["status"] = "NO_CHANGE"
                report["results"].append(record)
                continue

            result = api_put(f"Update{entity}/{entity_id}", payload, dry_run=not AUTO_APPLY)
            record["status"] = "APPLIED" if AUTO_APPLY else "DRY_RUN"
            record["apiResult"] = result

        except Exception as exc:
            record["status"] = "ERROR"
            record["error"] = str(exc)

        report["results"].append(record)

    Path("reports").mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out = Path("reports") / f"safe-seo-{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if any(x["status"] == "ERROR" for x in report["results"]):
        sys.exit(2)


if __name__ == "__main__":
    main()
