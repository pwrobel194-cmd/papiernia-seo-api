# Papiernia — prywatna skrzynka zdjęć, bez Work

Stan: implementacja klienta i workflow gotowa na gałęzi `feature/product-creator-v04`; **integracja Drive z GitHub nie jest jeszcze aktywna** do czasu podłączenia Google service account. NIGDY nie wrzucaj ZIP-ów do tego publicznego repozytorium.

## Foldery na Dysku Google

- Wejściowy (prywatny): https://drive.google.com/drive/folders/1O1yRs2uD9ENMQhHLX5Ac7rH8FZM5jZwd
- Po przetworzeniu: https://drive.google.com/drive/folders/1eDt9fjQdJWwKdwX01PKd21Gl6weKFucC

Paczka dla istniejącego nieopublikowanego produktu 4968 musi nazywać się `4968.zip`, zawierać `manifest.json` i pięć plików WebP. Nie używać produktu już opublikowanego.

## Jednorazowa konfiguracja połączenia

1. W Google Cloud na koncie właściciela Drive włącz **Google Drive API**.
2. Utwórz dedykowane **konto usługi (service account)** o nazwie np. `papiernia-media-bot`. **Nie przydzielaj mu roli Project Editor/Owner**.
3. Wygeneruj klucz JSON konta usługi. Zachowaj go bezpiecznie; **nie wysyłaj do ChatGPT ani nie commituj do GitHub**.
4. W GitHub w repozytorium `pwrobel194-cmd/papiernia-seo-api`, Settings > Secrets and variables > Actions > New repository secret, zapisz **CAŁĄ zawartość JSON** jako `PAPIERNIA_DRIVE_SERVICE_ACCOUNT_JSON`.
5. Na Dysku Google udostępnij **wyłącznie folder wejściowy**, z rolą Edytor, adresowi `client_email` z klucza JSON. Uprawnienie powinno obejmować podfolder `Przetworzone`. Nigdy nie ustawiaj `Każdy posiadający link`.
6. Już istniejący GitHub secret `PAPIERNIA_SEO_API_KEY` pozostaw bez zmian.
7. Uruchom z gałęzi `feature/product-creator-v04` GitHub Actions > `Papiernia private media inbox` > Run workflow, podając product_id=4968. Alternatywnie po recenzji i scaleniu do gałęzi głównej workflow będzie sprawdzał folder co godzinę.

## Oczekiwane działanie

GitHub Actions czyta wyłącznie nazwane <productId>.zip ze wskazanego prywatnego folderu. Cała zawartość zdjęć pozostaje poza historią Git; jest pobierana jedynie na tymczasowy runner GitHub. Przed zapisem klient sprawdza nieopublikowany produkt przez API. Wysyła kolejno WebP, wymaga obecności identyfikującego markera na galerii po zapisie, nie powtarza ślepo błędnych transferów. Po potwierdzeniu zdjęć ZIP jest przenoszony do prywatnego folderu `Przetworzone`.

Oczekiwany log: `CONFIRMED ... -> picture <id>` pięciokrotnie, `CONFIRMED product 4968: at least 5 image(s) associated`, `ARCHIVED 4968.zip ...`.

## Ograniczenia

- Obecny mechanizm zakłada przesłanie ZIP do folderu Google Drive; samo dodanie załącznika w rozmowie ChatGPT nie przeniesie pliku automatycznie na Drive bez osobnego, autoryzowanego konektora przekazującego bajty.
- Nie uruchamiaj workflow na publicznych zdjęciach klientów w GitHub. Google service account dostaje dostęp tylko do wybranego folderu Drive.
- Jeśli service account zgłosi błąd `storageQuotaExceeded` w kontach Drive, należy zastosować udostępniony dysk (Shared Drive) lub inny typ konta technicznego, albo alternatywne prywatne magazynowanie. Na koncie usługi bez limitu może nie działać wgrywanie; ten system wyłącznie odczytuje i przenosi pliki dostarczone przez użytkownika.
- Status wdrożenia kodu w repo nie oznacza przeprowadzonego testu transferu po Google Drive. Produkt 4968 ma w ostatnim odczycie 0 zdjęć.
