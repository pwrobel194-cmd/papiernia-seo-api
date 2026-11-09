import unittest
from upload_reconcile import ImageIdentity, UploadStatus, reconcile, upload_with_reconciliation


class UploadReconcileTests(unittest.TestCase):
    def setUp(self):
        self.expected = ImageIdentity("abcd1234", "zdjecie.webp", 4964)
        self.record = {"sha256": "abcd1234", "productId": 4964}

    def test_http_error_but_saved(self):
        def broken_upload():
            raise RuntimeError("HTTP 500 after save")
        result = upload_with_reconciliation(broken_upload, lambda: [self.record], self.expected)
        self.assertEqual(result, UploadStatus.CONFIRMED)

    def test_not_saved(self):
        result = upload_with_reconciliation(lambda: {"ok": False}, lambda: [], self.expected)
        self.assertEqual(result, UploadStatus.NOT_FOUND)

    def test_does_not_accept_same_filename_other_product(self):
        self.assertEqual(reconcile(self.expected, [{"sha256": "abcd1234", "productId": 10}]), UploadStatus.NOT_FOUND)

    def test_duplicate_matches_are_ambiguous(self):
        self.assertEqual(reconcile(self.expected, [self.record, self.record]), UploadStatus.AMBIGUOUS)

    def test_success_response_not_enough(self):
        self.assertEqual(upload_with_reconciliation(lambda: {"ok": True}, lambda: [], self.expected), UploadStatus.NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
