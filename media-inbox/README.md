# DEPRECATED: no ZIP files in this public repository

Media ingestion now uses the private Google Drive folder and its Google service
account. Never commit ZIPs, photos, customer assets or plain-image base64 here.

Action: .github/workflows/upload-product-media.yml
Worker: automation/drive_media_inbox.py
The Actions job uses Google credentials stored in GitHub Secrets, not Git files.
