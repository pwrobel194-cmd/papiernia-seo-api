# Media inbox (test environment)

Workflow `.github/workflows/upload-product-media.yml` listens for one added `media-inbox/<productId>.zip` on branch `feature/product-creator-v04`.

**SECURITY:** This repository is PUBLIC. Anything committed here (including later removed ZIPs) remains discoverable in Git history. Do NOT upload confidential / client photos, personalized print files, private addresses, order data, or proprietary unpublished designs. Prefer a private asset repository or direct authenticated image transport for real products.

ZIP format: root `manifest.json`, an array of objects with `file`, `order`, `alt`, `title`. Each file is a WebP of at most 2 MiB, with the name in the manifest.

A GitHub Actions secret `PAPIERNIA_SEO_API_KEY` must already exist. The plugin requires a nonpublished product and allows writes. The workflow uses a fixed API host https://papiernia.net.pl and restricts the file name to numeric Product IDs.

Upload only a disposable, non-sensitive TEST image until safe private transport is configured.
