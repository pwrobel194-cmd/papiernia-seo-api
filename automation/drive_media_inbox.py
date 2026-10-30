"""Private Google Drive ZIP inbox -> installed Papiernia nopCommerce API.

Requires a dedicated Google service account with Editor access ONLY to the inbox
and processed folders, and PAPIERNIA_DRIVE_SERVICE_ACCOUNT_JSON in GitHub secrets.
Neither ZIP bytes nor service-account credentials are committed to Git.
"""
from __future__ import annotations
import argparse
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

from product_media_client import run as upload_media

DEFAULT_INBOX = "1O1yRs2uD9ENMQhHLX5Ac7rH8FZM5jZwd"
DEFAULT_DONE = "1eDt9fjQdJWwKdwX01PKd21Gl6weKFucC"
ZIP_MAX_BYTES = 25_000_000
ZIP_MAX_ENTRIES = 80
PRODUCT_NAME = re.compile(r"^([1-9][0-9]{0,8})\.zip$", flags=re.ASCII)

def google_drive():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    raw = os.environ.get("PAPIERNIA_DRIVE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise RuntimeError("GitHub secret PAPIERNIA_DRIVE_SERVICE_ACCOUNT_JSON is missing")
    info = json.loads(raw)
    if info.get("type") != "service_account":
        raise RuntimeError("Expected Google service account credentials")
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=credentials, cache_discovery=False)

def inbox_files(drive, folder: str):
    token = None
    while True:
        response = drive.files().list(
            q=f"'{folder}' in parents and trashed = false",
            spaces="drive",
            pageSize=100,
            pageToken=token,
            fields="nextPageToken,files(id,name,size,mimeType,modifiedTime)",
            orderBy="createdTime",
        ).execute()
        yield from response.get("files", [])
        token = response.get("nextPageToken")
        if not token:
            return

def download_archive(drive, file_id: str, expected_bytes: int) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    if expected_bytes > ZIP_MAX_BYTES:
        raise ValueError("ZIP too large (limit 25MB)")
    buf = io.BytesIO()
    request = drive.files().get_media(fileId=file_id)
    downloader = MediaIoBaseDownload(buf, request, chunksize=1024*1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
        if buf.tell() > ZIP_MAX_BYTES:
            raise ValueError("ZIP exceeded 25MB")
    data = buf.getvalue()
    if len(data) > ZIP_MAX_BYTES:
        raise ValueError("ZIP exceeded 25MB")
    return data

def validate_archive(binary: bytes):
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        infos = z.infolist()
        if len(infos) > ZIP_MAX_ENTRIES:
            raise ValueError("ZIP contains too many entries")
        if not any(item.filename == "manifest.json" for item in infos):
            raise ValueError("ZIP manifest.json missing")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP contains duplicate names")
        manifest = json.loads(z.read("manifest.json"))
        items = manifest if isinstance(manifest, list) else manifest.get("images", [])
        if not items or len(items) > 30:
            raise ValueError("manifest must list 1-30 WebP images")
        ordered = []
        for image in items:
            filename = image.get("file", "")
            if not re.fullmatch(r"[a-zA-Z0-9_-]+\.webp", filename):
                raise ValueError("Unsafe WebP filename")
            if filename not in names:
                raise ValueError("Manifest references a missing WebP")
            file_info = z.getinfo(filename)
            if file_info.file_size > 2*1024*1024:
                raise ValueError("WebP exceeds API limit")
            ordered.append((image.get("order", image.get("displayOrder",0)), filename))
        if len(set(name for _,name in ordered)) != len(ordered):
            raise ValueError("Duplicate WebP in manifest")
        if ordered != sorted(ordered):
            raise ValueError("Manifest images must be listed in intended display order")
    return len(ordered)

def process(drive, key: str, *, folder: str, done_folder: str, only_id: int|None = None):
    processed = 0
    for item in inbox_files(drive, folder):
        m = PRODUCT_NAME.fullmatch(item.get("name",""))
        if not m:
            print("SKIP: file is not named <productId>.zip")
            continue
        product_id = int(m.group(1))
        if only_id is not None and product_id != only_id:
            continue
        file_size = int(item.get("size") or 0)
        if file_size > ZIP_MAX_BYTES:
            print(f"SKIP: product {product_id} oversized ZIP")
            continue
        print(f"PROCESS productId={product_id}, bytes={file_size}")
        binary = download_archive(drive, item["id"], file_size)
        image_count = validate_archive(binary)
        with tempfile.TemporaryDirectory(prefix="pn_media_") as td:
            filename = Path(td) / f"{product_id}.zip"
            filename.write_bytes(binary)
            result = upload_media(str(filename), product_id, key)
        if result.get("published") is not False:
            raise RuntimeError("Product changed to published: refusing completion")
        if len(result.get("pictures", [])) < image_count:
            raise RuntimeError(f"Gallery has fewer than {image_count} expected images")
        print(f"CONFIRMED product {product_id}: at least {image_count} image(s) associated")
        drive.files().update(fileId=item["id"], addParents=done_folder,
                             removeParents=folder, fields="id,parents").execute()
        print(f"ARCHIVED {item['name']} in Drive processed folder")
        processed += 1
    print(f"DONE processed={processed}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--product-id",type=int)
    args=parser.parse_args()
    key=os.environ.get("PAPIERNIA_SEO_API_KEY")
    if not key:
        raise SystemExit("GitHub secret PAPIERNIA_SEO_API_KEY is missing")
    drive=google_drive()
    process(drive,key,folder=os.environ.get("PAPIERNIA_MEDIA_INBOX_ID",DEFAULT_INBOX),
            done_folder=os.environ.get("PAPIERNIA_MEDIA_DONE_ID",DEFAULT_DONE),
            only_id=args.product_id)

if __name__ == "__main__":
    main()
