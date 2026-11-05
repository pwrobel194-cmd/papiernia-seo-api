# Papiernia SEO API 3.0 — release candidate (nopCommerce 4.50.3)

**Status (2026-11-05):** plugin v3 installed by the shop owner; GitHub Actions compilation succeeded. On unpublished test product ID 4968, live API preview, commit and read-back succeeded for product name/H1, SKU, short/full HTML descriptions, meta fields and slug. The public page responded 404 because product Published=false. Image ALT/Title and category writes have **not** yet been live-tested. The PR remains draft, not merged; no further product modifications are authorized.

## Read-only endpoints
All v1 endpoints remain available under /papiernia-seo-api/v1.

- GET /papiernia-seo-api/v3/ProductSnapshot/{id}: product name (H1), SKU, HTML descriptions, meta, slug, status, categories, picture metadata.
- GET /papiernia-seo-api/v3/CategorySnapshot/{id}: category name (H1), HTML, meta, slug, parent, status, main picture metadata.
- GET /papiernia-seo-api/v3/ProductPictures/{id}: existing v1 picture metadata, available on v3 route as well.
- GET /papiernia-seo-api/v3/CategoryPicture/{id}: category picture ALT, Title, SEO filename.
- GET /papiernia-seo-api/v3/ProductHtmlImages/{id}: src, alt and title attributes of images embedded in product HTML.
- GET /papiernia-seo-api/v3/ProductCategories/{id}: current product-category assignments (read-only).

## Two-stage controlled writes
Product:
1. POST /papiernia-seo-api/v3/PreviewProductSeo/{id}
2. PUT /papiernia-seo-api/v3/CommitProductSeo/{id}

Example JSON:
    {
      "metaTitle": "Podziękowania dla gości na wesele – Papiernia",
      "name": "Podziękowania dla gości weselnych",
      "reason": "Zatwierdzone przez właściciela"
    }

Preview returns before, after and a 15-minute approvalToken. Commit must send the same edited fields with approvalToken and reason. If the source changed between calls, commit fails with HTTP 409. Clients must show diffs to the owner and commit only after explicit approval.

Category:
- POST /v3/PreviewCategorySeo/{id}
- PUT /v3/CommitCategorySeo/{id}

Editable product fields: Name, SKU, ShortDescription, FullDescription, MetaTitle, MetaDescription, MetaKeywords, SeName.
Editable category fields: Name, Description, MetaTitle, MetaDescription, MetaKeywords, SeName.
Null means keep current field; empty string means clear a field (subject to validation).
HTML updates preserve all existing image src attributes and relative image order, and may add extra images.

Pictures:
- POST /v3/PreviewPictureMetadata/{id}
- PUT /v3/CommitPictureMetadata/{id}

The route id is product id when scope=product and category id when scope=category.
Payload:
    {
      "scope": "product",
      "pictureId": 123,
      "altAttribute": "Ciasteczko z wróżbą jako podziękowanie weselne",
      "titleAttribute": "Ciasteczko z wróżbą – Papiernia",
      "reason": "Zatwierdzone przez właściciela"
    }
Use preview and add returned approvalToken on commit. Only ALT and Title can be changed. No picture deletions, replacements, reordering or SEO filename rewriting.
A shared Picture ID can appear in several places; check associations. Some themes generate category ALT/Title dynamically; verify public output.

## Not in this release (read-only or deferred)
- Redirect creation/import, robots.txt, canonical/noindex, sitemaps, JSON-LD, file system and server maintenance.
- Product-category assignment writes, moving/publishing categories, prices, inventory, orders, customers.
- Global picture-library writes and changing physical filenames.
- Separate endpoint for embedded HTML image attributes: use a guarded FullDescription update.
- Unconditional bulk auto-deployment.

## Security
- Existing X-Papiernia-SEO-Key header; never put it in repository.
- Existing Enabled and AllowWrites settings.
- Preview is read-only; commit checks HMAC-signed token valid 15 minutes, before-state fingerprint, reason and scoped operation.
- After successful commit the plugin stores an audit record in App_Data/PapierniaSeoApi.
- v1 is preserved; old automated workflows must still respect owner approval.

## Build and installation
.github/workflows/build-plugin.yml compiles against nopCommerce release-4.50.3 using .NET 6 and creates installable ZIP with Misc.PapierniaSeoApi as root folder. Download only the SUCCESSFUL compiled GitHub Actions artifact; do not install a source archive.

1. Back up site files, database, current plugin DLL/folder, App_Data/PapierniaSeoApi and plugin settings.
2. Test on a staging clone matching nopCommerce 4.50.3.
3. Do not uninstall the existing plugin: its uninstall procedure deletes API settings/key. Use controlled replacement/upgrade of the existing plugin folder; retain the SystemName.
4. Restart app; verify old /v1/Health and new /v3/ProductSnapshot/4955.
5. Test preview requests first; verify no production fields change.
6. Only after owner explicitly approves, try a single low-impact commit and verify HTML, picture ALT/Title and audit.
7. If anything fails, restore the backed-up plugin and application state.

Official plugin build instructions: https://docs.nopcommerce.com/en/developer/plugins/how-to-write-plugin-4.50.html
