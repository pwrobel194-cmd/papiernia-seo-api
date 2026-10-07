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

COMMON_FIELDS = {"url", "metaTitle", "metaDescription", "metaKeywords", "reason", "auditOnly"}
CATEGORY_FIELDS = COMMON_FIELDS | {"description"}
PRODUCT_FIELDS = COMMON_FIELDS | {"shortDescription", "fullDescription", "replaceInFullDescription"}


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


def validate_replacements(action):
    replacements = action.get("replaceInFullDescription")
    if replacements is None:
        return
    if not isinstance(replacements, list) or not replacements:
        raise ValueError("replaceInFullDescription must be a non-empty list")
    if len(replacements) > 10:
        raise ValueError("Too many full-description replacements in one action")
    for item in replacements:
        if not isinstance(item, dict):
            raise ValueError("Each full-description replacement must be an object")
        old = item.get("from")
        new = item.get("to")
        if not isinstance(old, str) or not old:
            raise ValueError("Replacement 'from' must be a non-empty string")
        if not isinstance(new, str):
            raise ValueError("Replacement 'to' must be a string")
        expected = item.get("expectedCount")
        if expected is not None and (not isinstance(expected, int) or expected < 1):
            raise ValueError("expectedCount must be an integer >= 1")


def validate_common(action):
    if not action.get("url", "").startswith(BASE_URL + "/"):
        raise ValueError("URL outside papiernia.net.pl")

    if action.get("auditOnly") not in (None, True, False):
        raise ValueError("auditOnly must be boolean")

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
        if field in action and len(action.get(field) or "") > 100000:
            raise ValueError(f"{field} too long")

    validate_replacements(action)

    editable = {
        "metaTitle", "metaDescription", "metaKeywords", "description",
        "shortDescription", "fullDescription", "replaceInFullDescription"
    }
    if not action.get("auditOnly") and not any(field in action for field in editable):
        raise ValueError("Action contains no editable SEO fields")


def validate_for_entity(action, entity):
    validate_common(action)
    allowed = CATEGORY_FIELDS if entity == "Category" else PRODUCT_FIELDS
    unknown = set(action) - allowed
    if unknown:
        raise ValueError(f"Unsupported fields for {entity}: {sorted(unknown)}")
    if entity != "Product" and "replaceInFullDescription" in action:
        raise ValueError("replaceInFullDescription is supported only for Product")


def read_current(entity, current):
    def get(name):
        value = current.get(name)
        if value is None:
            value = current.get(name[0].upper() + name[1:])
        return value

    data = {
        "name": get("name"),
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


def apply_full_description_replacements(action, current_full_description):
    result = current_full_description or ""
    audit = []
    for item in action.get("replaceInFullDescription", []):
        old = item["from"]
        new = item["to"]
        count = result.count(old)
        expected = item.get("expectedCount")
        if count == 0:
            raise ValueError(f"Replacement text not found in fullDescription: {old!r}")
        if expected is not None and count != expected:
            raise ValueError(
                f"Replacement count mismatch for {old!r}: found {count}, expected {expected}"
            )
        result = result.replace(old, new)
        audit.append({"from": old, "to": new, "count": count})
    return result, audit


def build_payload(action, entity, entity_id, before_all):
    editable = ["metaTitle", "metaDescription", "metaKeywords"]
    editable += ["description"] if entity == "Category" else ["shortDescription", "fullDescription"]

    payload = {
        field: action[field].strip() if isinstance(action[field], str) else action[field]
        for field in editable
        if field in action
    }

    replacement_audit = []
    if entity == "Product" and "replaceInFullDescription" in action:
        if "fullDescription" in action:
            raise ValueError("Do not combine fullDescription with replaceInFullDescription")
        replaced, replacement_audit = apply_full_description_replacements(
            action, before_all.get("fullDescription")
        )
        if len(replaced) > 100000:
            raise ValueError("Generated fullDescription too long")
        payload["fullDescription"] = replaced

    payload["requestId"] = (
        f"chatgpt-seo-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        f"-{entity.lower()}-{entity_id}"
    )
    payload["reason"] = action.get("reason", "ChatGPT SEO automation")
    return payload, replacement_audit


def main():
    source = json.loads(Path("automation/actions.json").read_text(encoding="utf-8"))
    actions = source.get("actions", [])
    if not 1 <= len(actions) <= 5:
        raise RuntimeError("Safe run requires 1-5 actions")

    batch_apply = source.get("apply", False) is True
    apply_now = AUTO_APPLY and batch_apply

    health = api_get("Health")
    report = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "pluginHealth": health,
        "autoApplyEnabled": AUTO_APPLY,
        "batchApplyRequested": batch_apply,
        "mode": "APPLY" if apply_now else "DRY_RUN",
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
            if action.get("auditOnly"):
                record["status"] = "AUDIT_ONLY"
                record["current"] = before_all
                report["results"].append(record)
                continue

            payload, replacement_audit = build_payload(action, entity, entity_id, before_all)
            edit_fields = [k for k in payload if k not in ("requestId", "reason")]
            before = {field: before_all.get(field) for field in edit_fields}
            after = {field: payload[field] for field in edit_fields}
            record["before"] = before
            record["after"] = after
            if replacement_audit:
                record["targetedReplacements"] = replacement_audit

            if before == after:
                record["status"] = "NO_CHANGE"
                report["results"].append(record)
                continue

            result = api_put(f"Update{entity}/{entity_id}", payload, dry_run=not apply_now)
            record["status"] = "APPLIED" if apply_now else "DRY_RUN"
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
