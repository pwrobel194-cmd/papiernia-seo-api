import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive_media_inbox import validate_archive, PRODUCT_NAME


def make_zip(manifest, assets=None):
    assets = assets or {"01-main.webp": b"RIFF1234WEBP" + b"a" * 20}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        for name, data in assets.items():
            z.writestr(name, data)
    return buf.getvalue()


class DriveInboxTests(unittest.TestCase):
    def test_named_product_zip(self):
        self.assertEqual(PRODUCT_NAME.fullmatch("4968.zip").group(1), "4968")
        self.assertIsNone(PRODUCT_NAME.fullmatch("customer-photo.zip"))
        self.assertIsNone(PRODUCT_NAME.fullmatch("../4968.zip"))

    def test_valid_list_manifest(self):
        zip_bytes = make_zip([{"file": "01-main.webp", "order": 0}])
        self.assertEqual(validate_archive(zip_bytes), 1)

    def test_missing_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing WebP"):
            validate_archive(make_zip([{"file": "not-found.webp", "order": 0}]))

    def test_path_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsafe WebP"):
            validate_archive(make_zip([{"file": "../../01-main.webp", "order": 0}]))

    def test_reversed_image_order_rejected(self):
        manifest = [{"file": "02-secondary.webp", "order": 1}, {"file": "01-main.webp", "order": 0}]
        assets = {"01-main.webp": b"foo", "02-secondary.webp": b"bar"}
        with self.assertRaisesRegex(ValueError, "display order"):
            validate_archive(make_zip(manifest, assets))

    def test_extra_large_webp_is_rejected(self):
        assets = {"01-main.webp": b"x" * (2 * 1024 * 1024 + 1)}
        with self.assertRaisesRegex(ValueError, "API limit"):
            validate_archive(make_zip([{"file": "01-main.webp", "order": 0}], assets))


if __name__ == "__main__":
    unittest.main()
