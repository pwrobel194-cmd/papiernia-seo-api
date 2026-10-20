# AUTO SEO Papiernia — Product Creator 0.4 (development)

## Scope
- `POST /papiernia-seo-api/v1/CreateDraft?dryRun=true`: preview request.
- `POST /papiernia-seo-api/v1/CreateDraft?dryRun=false`: creates an **unpublished** simple product associated with one category.
- Key header: `X-Papiernia-SEO-Key`.
- No product auto-publishing, image deletion, or changes to existing images.
- The endpoint does NOT yet implement retries/idempotency, product attributes, templates, GSC checks or image upload. Treat as DEVELOPMENT and do not deploy to production before safeguards and build tests.

## Critical upload behavior reported by store operator
nopCommerce may return a server error although the WebP image has already been saved. A failed HTTP response is not proof of rollback. On an error: read the actual product/gallery inventory, locate the asset by SHA-256 plus product association, verify accessible content, then confirm or flag for manual review. Never blindly resubmit on an ambiguous state; avoid duplicate pictures. Implement this protocol when adding the media endpoint.

## Follow-ups prior to production
1. Implement idempotency key + persistent request receipts for draft creation to prevent duplicates when response is lost.
2. Separate image storage upload from product association, and add authoritative hash/inventory endpoint.
3. Restrict uploaded file formats and size; reject ZIP path traversal, symlinks and unsupported image codecs.
4. HTML allowlist/sanitization and image processing policy; keep graphical model originals unchanged.
5. Audit draft writes, ensure categories, templates and store configuration are valid.
6. Add independent operator approval before publishing.
7. Run GitHub Actions nopCommerce 4.50.3 compilation and integration tests in staging.
8. Remove displayed API key from admin page; rotate if compromised.
9. Connect keyword ownership map and GSC trend feed for category-level SEO checks.

## Recommended form inputs
Category, rough product name (optional), price, text description, min quantity, needs assembly, reference product, ZIP. Output: SEO proposal -> approved draft -> upload reconciliation -> gallery verification -> publication approval.
