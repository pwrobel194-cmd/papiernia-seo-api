# Papiernia SEO API

Plugin do bezpiecznej automatyzacji SEO sklepu papiernia.net.pl na nopCommerce 4.50.3.

## Założenia bezpieczeństwa
- API wymaga nagłówka `X-Papiernia-SEO-Key`.
- Brak endpointów do cen, zamówień, klientów, płatności i kasowania produktów.
- Zmiany produktów/kategorii mogą działać w trybie `dryRun=true`.
- Każdy zapis trafia do audytu w `App_Data/PapierniaSeoApi`.

## Build
GitHub Actions buduje plugin przeciwko oficjalnym źródłom nopCommerce tag `release-4.50.3` i publikuje gotowy ZIP jako artifact.
