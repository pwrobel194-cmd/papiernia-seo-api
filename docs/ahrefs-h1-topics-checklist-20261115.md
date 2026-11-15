# Ahrefs H1 – status i bezpieczne poprawki stron informacyjnych (15.11.2026)

## Zrobione i potwierdzone

- Produkty: **27 z 27** mają jeden H1 i `Personalizowane upominki` jako H2 (zapis ręczny we wspólnej zakładce Nop Quick Tabs; weryfikacja odczytem HTML).
- Kategoria `/kategorie` (ID 335): **zapis przez istniejące SEO API 3.0 zakończony sukcesem**. W jej Description drugi H1 zamieniono na H2. Readback API i bezpośredni HTML wykazały jeden H1: `Podziękowania dla Gości`. Nie zmieniono nazwy ani meta.
- Raport kategorii + tematów: [ahrefs-h1-remediation-20261115.json](../automation/reports/ahrefs-h1-remediation-20261115.json).

## Pozostało 9 tematów (Topics): wymagają edycji w panelu

Odczyt live z 2026-11-15T18:09:16.143823+00:00. Żaden temat nie został zmodyfikowany, ponieważ istniejące SEO API 3.0 nie zapewnia endpointu do edycji `Topic`. Nie tworzymy nowego API i nie obchodzimy jego uprawnień.

**Nawigacja:** panel administracyjny → Zarządzanie treścią → Tematy (strony). Wyszukaj stronę po nazwie systemowej/URL. Wejdź w kod źródłowy HTML opisu.

**Operacja dla każdego tematu:** znajdź w treści poniższy *drugi* nagłówek H1. Zamień wyłącznie jego otwierający tag `<h1...>` na `<h2...>` i zamykający `</h1>` na `</h2>`. Zachowaj cały tekst oraz wszystkie atrybuty w otwierającym tagu (np. `style`). Nie dotykaj pierwszego H1, który generuje system nopCommerce.

| Lp. | Adres strony | Tekst drugiego H1 (zmienić na H2) |
|---:|---|---|
| 1 | [`poradnik`](https://papiernia.net.pl/poradnik) | Pomysły, które pomagają wybrać dobrze. |
| 2 | [`ile-podziekowan-dla-gosci-zamowic`](https://papiernia.net.pl/ile-podziekowan-dla-gosci-zamowic) | Ile podziękowań dla gości zamówić? |
| 3 | [`co-napisac-na-podziekowaniu-dla-gosci`](https://papiernia.net.pl/co-napisac-na-podziekowaniu-dla-gosci) | Co napisać na podziękowaniu dla gości? |
| 4 | [`podziekowania-dla-gosci-do-5-zl`](https://papiernia.net.pl/podziekowania-dla-gosci-do-5-zl) | Podziękowania dla gości do 5 zł – jak wybierać? |
| 5 | [`jak-wybrac-upominki-dla-gosci-na-chrzest`](https://papiernia.net.pl/jak-wybrac-upominki-dla-gosci-na-chrzest) | Jak wybrać upominki dla gości na chrzest? |
| 6 | [`jak-wybrac-podziekowania-dla-gosci-na-komunie`](https://papiernia.net.pl/jak-wybrac-podziekowania-dla-gosci-na-komunie) | Jak wybrać podziękowania dla gości na Komunię? |
| 7 | [`jak-zaplanowac-podziekowania-na-urodziny`](https://papiernia.net.pl/jak-zaplanowac-podziekowania-na-urodziny) | Jak zaplanować podziękowania na urodziny? |
| 8 | [`jak-wybrac-upominki-dla-klientow-firmowych`](https://papiernia.net.pl/jak-wybrac-upominki-dla-klientow-firmowych) | Jak wybrać upominki dla klientów firmy? |
| 9 | [`jakie-podziekowania-dla-gosci-weselnych-wybrac`](https://papiernia.net.pl/jakie-podziekowania-dla-gosci-weselnych-wybrac) | Jakie podziękowania dla gości weselnych wybrać? |

### Przykład – zachowaj style

Przed:
```html
<h1 style="font-size:38px;line-height:1.16">Pomysły, które pomagają wybrać dobrze.</h1>
```

Po:
```html
<h2 style="font-size:38px;line-height:1.16">Pomysły, które pomagają wybrać dobrze.</h2>
```

Dokładne style HTML mogą się różnić – nie zamieniaj całego wiersza szablonem, zmień tylko tagi.

**Ważne:** wcześniejszy raport Ahrefs wskazywał `co-napisać-na-podziekowaniu-dla-gosci` z literą `ć` w URL, która aktualnie zwracała 404. Działający adres, zweryfikowany teraz, to `co-napisac-na-podziekowaniu-dla-gosci` – bez znaku diakrytycznego. Nie zmieniaj działającego adresu URL.

## Zasady bezpieczeństwa

Zachowaj wszystkie treści, linki, FAQ, zdjęcia i style. Nie zmieniaj meta, H1 systemowych, slugów, produktów, kategorii, przypisań, atrybutów, cen, galerii, informacji „do samodzielnego złożenia”. Zmiany tylko w otwierającym i zamykającym tagu nagłówka. Po zmianie sprawdź każdą stronę i zrób nowy audyt Ahrefs.
