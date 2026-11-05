# Papiernia SEO API — centralny standard automatyzacji

Właściciel sklepu: papiernia.net.pl · silnik: nopCommerce 4.50.3.

## Aktualny standard pracy: SEO API 3.0 (od 5 listopada 2026)

Wersja 3.0 została wgrana do sklepu przez właściciela. 5 listopada 2026 przeprowadzono na **nieopublikowanym produkcie testowym ID 4968** ("TEST – Kot w butach") rzeczywisty, zakończony sukcesem test zapisu i ponownego odczytu:
- nazwa produktu (H1), SKU;
- krótki i pełny opis HTML;
- Meta Title, Meta Description, Meta Keywords;
- slug produktu.

API zwróciło poprawny zapis i odczyt. Publiczna strona testowego produktu słusznie zwracała 404 z uwagi na `Published = false`. **ALT/Title zdjęć nie zostały jeszcze przetestowane na żywo**, ponieważ produkt testowy nie miał przypisanych zdjęć. Nie uznajemy też za potwierdzone wszystkich nieprzetestowanych operacji, np. edycji kategorii.

**Uwaga — repozytorium:** Kod v3 i jego nowe endpointy znajdują się w [PR #3](https://github.com/pwrobel194-cmd/papiernia-seo-api/pull/3), gałąź `feature/seo-api-v3-20261105`. PR pozostaje roboczy i niescalony z `main`; nie wolno zakładać, że pliki `src/` na `main` opisują zainstalowaną v3. Wersja v1 pozostaje kompatybilna z dotychczasowymi workflow.

## Używaj SEO API 3.0 do nowych działań

Dokumentacja endpointów i zabezpieczeń: [docs/seo-api-v3-release-notes.md na gałęzi v3](https://github.com/pwrobel194-cmd/papiernia-seo-api/blob/feature/seo-api-v3-20261105/docs/seo-api-v3-release-notes.md).

- Odczyt produktów: `GET /papiernia-seo-api/v3/ProductSnapshot/{id}`.
- Odczyt kategorii: `GET /papiernia-seo-api/v3/CategorySnapshot/{id}`.
- Odczyt zdjęć kategorii: `GET /papiernia-seo-api/v3/CategoryPicture/{id}`.
- Odczyt zdjęć w HTML: `GET /papiernia-seo-api/v3/ProductHtmlImages/{id}`.
- Odczyt przypisania kategorii do produktu: `GET /papiernia-seo-api/v3/ProductCategories/{id}`.
- Edycja produktu: `POST PreviewProductSeo/{id}`, następnie **po zatwierdzeniu** `PUT CommitProductSeo/{id}`.
- Edycja kategorii: `POST PreviewCategorySeo/{id}`, potem `PUT CommitCategorySeo/{id}`.
- ALT i Title zdjęć produktów/kategorii: `POST PreviewPictureMetadata/{id}`, następnie `PUT CommitPictureMetadata/{id}`.

Dla każdego zapisu: (1) odczytaj bieżące dane, (2) zabezpiecz poprzedni stan, (3) wygeneruj dokładną różnicę / preview, (4) uzyskaj wyraźną decyzję właściciela, (5) wykonaj zapis za pomocą tokenu z preview (ważność 15 minut), (6) odczytaj ponownie i zweryfikuj, (7) zapisz raport zmian. Jeśli dane zmieniły się od podglądu — przerwij, nie nadpisuj.

**Stałe zasady:** nie usuwać zdjęć, nie przestawiać ich kolejności, zachowywać istniejące HTML i rozbudowaną treść kategorii; nie nadpisywać opisów wykonanych w poprzednich audytach bez porównania. Zachowywać informację „do samodzielnego złożenia”, kiedy dotyczy produktu. Nie modyfikować cen, zamówień, klientów ani stanów magazynowych.

## Ograniczenia i starsza automatyzacja

API v3 nie dodaje automatycznie obsługi 301/410, `robots.txt`, `noindex`, `sitemap`, JSON-LD, serwera, publikacji produktów ani zapisu przypisań kategorii. Nie deklaruj tych możliwości bez wdrożenia i odrębnych testów.

Dotychczasowe skrypty i workflow używające `/v1` **pozostają bez zmian**, dopóki nie zostaną osobno przeniesione i przetestowane. Nie wolno uruchamiać zbiorowych zapisów automatycznie bez właścicielskiej decyzji.

Klucz `X-Papiernia-SEO-Key` przechowywany jest poza repozytorium (sekret GitHub Actions); nigdy nie wpisuj go do README, logów ani zgłoszeń. Obecny dziennik API to `App_Data/PapierniaSeoApi`.

## Potwierdzenie

[Zakończony test zapisu v3](https://github.com/pwrobel194-cmd/papiernia-seo-api/actions/runs/42074609483) · [końcowy test statusu nieopublikowanego produktu](https://github.com/pwrobel194-cmd/papiernia-seo-api/actions/runs/42074993237) · [PR #3](https://github.com/pwrobel194-cmd/papiernia-seo-api/pull/3).
