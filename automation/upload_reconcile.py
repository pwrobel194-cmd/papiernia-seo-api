"""Never infer upload failure from an HTTP error alone.

After an ambiguous upload response, read the media inventory and verify both
image identity and intended product association before deciding to retry.
This helper is intentionally API-agnostic: the caller supplies these functions.
"""
from dataclasses import dataclass
from enum import Enum


class UploadStatus(str, Enum):
    CONFIRMED = "confirmed"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ImageIdentity:
    sha256: str
    filename: str
    product_id: int


def reconcile(expected: ImageIdentity, uploaded_assets: list[dict]) -> UploadStatus:
    """Require a server-provided SHA-256 for positive verification.

    A URL or a filename alone is insufficient: they can point to stale content.
    Avoid a duplicate upload when server state cannot be established.
    """
    matches = [
        item for item in uploaded_assets
        if str(item.get("sha256", "")).lower() == expected.sha256.lower()
        and item.get("productId") == expected.product_id
    ]
    if len(matches) == 1:
        return UploadStatus.CONFIRMED
    if len(matches) > 1:
        return UploadStatus.AMBIGUOUS
    if any(item.get("inventoryIncomplete") for item in uploaded_assets):
        return UploadStatus.AMBIGUOUS
    return UploadStatus.NOT_FOUND


def upload_with_reconciliation(upload, list_product_assets, identity: ImageIdentity):
    """Upload once; on any uncertain outcome VERIFY rather than blind retry.

    list_product_assets must perform a fresh authoritative read that includes
    SHA-256 and product associations; an unavailable inventory MUST raise.
    """
    try:
        response = upload()
        if response.get("ok") is True:
            status = reconcile(identity, list_product_assets())
            if status == UploadStatus.CONFIRMED:
                return status
    except Exception:
        pass
    # A successful-looking response still requires confirmation.
    return reconcile(identity, list_product_assets())
