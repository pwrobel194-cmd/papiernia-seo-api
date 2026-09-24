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


def validate(action):
    allowed = {"url", "metaTitle", "metaDescription", "reason"}
    unknown = set(action) - allowed
    if unknown:
        raise ValueError(f"Unsupported fields: {sorted(unknown)}")

    title = (action.get("metaTitle") or "").strip()
    desc = (action.get("metaDescription") or "").strip()

    if not 25 <= len(title) <= 70:
        raise ValueError(f"Title length {len(title)} outside safe range 25-70")
    if not 80 <= len(desc) <= 175:
        raise ValueError(f"Meta description length {len(desc)} outside safe range 80-175")
    if not action.get("url", "").startswith(BASE_URL + "/"):
        raise ValueError("URL outside papiernia.net.pl")


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
            validate(action)
            resolved = api_get("Resolve", {"url": action["url"]})
            entity = resolved.get("entity")
            entity_id = resolved.get("id")
            if entity not in ("Product", "Category") or not entity_id:
                raise RuntimeError(f"Unsupported entity: {resolved}")

            current = api_get(f"{entity}/{entity_id}")
            record["entity"] = entity
            record["id"] = entity_id
            record["before"] = {
                "metaTitle": current.get("metaTitle"),
                "metaDescription": current.get("metaDescription"),
            }

            payload = {
                "metaTitle": action["metaTitle"].strip(),
                "metaDescription": action["metaDescription"].strip(),
                "requestId": f"chatgpt-seo-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{entity.lower()}-{entity_id}",
                "reason": action.get("reason", "ChatGPT SEO automation"),
            }

            if record["before"]["metaTitle"] == payload["metaTitle"] and record["before"]["metaDescription"] == payload["metaDescription"]:
                record["status"] = "NO_CHANGE"
                report["results"].append(record)
                continue

            result = api_put(f"Update{entity}/{entity_id}", payload, dry_run=not AUTO_APPLY)
            record["after"] = {
                "metaTitle": payload["metaTitle"],
                "metaDescription": payload["metaDescription"],
            }
            record["status"] = "APPLIED" if AUTO_APPLY else "DRY_RUN"
            record["apiResult"] = result

        except Exception as exc:
            record["status"] = "ERROR"
            record["error"] = str(exc)

        report["results"].append(record)

    Path("reports").mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out = Path("reports") / f"safe-meta-{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if any(x["status"] == "ERROR" for x in report["results"]):
        sys.exit(2)


if __name__ == "__main__":
    main()
