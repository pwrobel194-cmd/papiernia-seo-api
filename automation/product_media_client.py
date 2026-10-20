"""Papiernia reusable media uploader. Uses installed API and a local ZIP.
No secret is stored in the repository. Run with PAPIERNIA_SEO_API_KEY in environment.
"""
import argparse, base64, hashlib, json, os, urllib.request, zipfile

BASE = "https://papiernia.net.pl/papiernia-seo-api/v1/"

def api(path, key, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"X-Papiernia-SEO-Key": key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers,
                                     method="POST" if data is not None else "GET")
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read())

def run(zip_path, product_id, key):
    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        state = api("DraftPictures/" + str(product_id), key)
        if state.get("published") is not False:
            raise RuntimeError("Product is published or gallery endpoint unavailable")
        for entry in manifest["images"]:
            name = entry["file"]
            binary = archive.read(name)
            checksum = hashlib.sha256(binary).hexdigest()
            request = {
                "base64Webp": base64.b64encode(binary).decode("ascii"),
                "sha256": checksum,
                "alt": entry.get("alt", ""),
                "title": entry.get("title", ""),
                "displayOrder": entry.get("displayOrder", 0)
            }
            dry = api(f"UploadDraftWebp/{product_id}?dryRun=true", key, request)
            if not dry.get("ok"):
                raise RuntimeError(f"Dry run failed for {name}")
            try:
                result = api(f"UploadDraftWebp/{product_id}?dryRun=false", key, request)
            except Exception as error:
                print(f"Ambiguous response for {name}: {error}. Checking inventory.")
                result = {}
            gallery = api("DraftPictures/" + str(product_id), key)
            marker = "pn-" + str(product_id) + "-" + checksum[:24]
            matched = [p for p in gallery.get("pictures", []) if p.get("SeoFilename") == marker]
            if len(matched) != 1:
                raise RuntimeError(f"Could not confirm {name}; stopped before retry")
            print(f"CONFIRMED {name} -> picture {matched[0]['pictureId']}")
        return api("DraftPictures/" + str(product_id), key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_file")
    parser.add_argument("--product-id", type=int, default=4968)
    options = parser.parse_args()
    token = os.environ.get("PAPIERNIA_SEO_API_KEY")
    if not token:
        parser.error("PAPIERNIA_SEO_API_KEY must be set")
    result = run(options.zip_file, options.product_id, token)
    print("FINAL IMAGE COUNT:", len(result.get("pictures", [])))
