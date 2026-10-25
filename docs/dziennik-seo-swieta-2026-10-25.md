# Papiernia.net.pl — dziennik wdrożeń SEO Święta — 25.10.2026

## Cel i założenia
- Kategoria główna/hub: https://papiernia.net.pl/upominki-swiateczne.
- Cel: wzrost łącznych organicznych wyświetleń, kliknięć i sprzedaży kategorii **oraz** produktów, nie wyłącznie pozycji jednej podstrony.
- Ryzyko optymalizacyjne zaakceptowane przez właściciela: wdrażanie całościowe i szybkie, ale bez niepotrzebnej zmiany URL lub utraty danych produktu.
- Strategia: kategoria odpowiada przede wszystkim na szerokie frazy B2B: „upominki świąteczne dla klientów”, „upominki dla firm”, „z logo”, „do 5 zł”; produkty zachowują silne określenia „świąteczny”, „dla klientów”, „firmowy”, lecz ich H1, metadane i główny temat wyróżniają *konkretny rodzaj upominku*; nie eliminować mechanicznie wspólnych słów z produktów.
- Nie uważać samego podobieństwa fraz za dowód szkodliwej kanibalizacji; decyzje na podstawie fraza × URL w GSC.

## Wdrożenie API: 33 produkty — potwierdzone technicznie
- Repozytorium: https://github.com/pwrobel194-cmd/papiernia-seo-api.
- Workflow: `.github/workflows/christmas-bulk-20261025.yml`.
- Lista produktów i mapa intencji: `automation/christmas_20261025_plan.json` (33 produkty).
- Skrypt: `automation/christmas_bulk_20261025.py`.
- Pierwszy run **nieudany** (błąd składni, przed zapisem): https://github.com/pwrobel194-cmd/papiernia-seo-api/actions/runs/40219994598.
- Drugi run **udany** (pełna walidacja + ponowny odczyt przez API): https://github.com/pwrobel194-cmd/papiernia-seo-api/actions/runs/40220065506.
- Wynik logów: `APPLIED_VERIFIED=33`, `NO_CHANGE=0`, `ERROR=0`.
- Zmieniono Meta Description dla 33 produktów, Meta Title dla 32, Full Description dla 12.
- Dla części produktów dopisano unikatową zajawkę tematyczną, a brakujące linki wewnętrzne do kategorii głównej uzupełniono, bez zmiany istniejących znaczników `img`.
- Kontrola zachowania: Name/H1, SeName/slug/URL, ShortDescription, zdjęcia i ich układ; nie modyfikowano cen.
- Raport i backup z pierwszym odczytem w GitHub Actions artifact `papiernia-christmas-bulk-20261025` (retencja 30 dni). Nie mylić sukcesu zapisu z poprawą SEO.

## H1: aktualizacja ręczna — potwierdzenie właściciela
- Przygotowano Excel `Papiernia_SEO_Swieta_H1_33_produktow_i_Tagi_2026.xlsx`.
- Plan obejmował 25 nazw/H1 do zmiany i 8 do pozostawienia.
- Właściciel potwierdził w rozmowie 25.10.2026 „OK - wdrożone” w odpowiedzi na plan H1.
- **Status**: wdrożenie ręczne zgłoszone przez właściciela. Brak niezależnego odczytu przez API wszystkich 33 nazw *po* zmianach; nie oznaczać jako automatycznie zweryfikowane.
- Ważne: `Nazwa strony przyjazna silnikowi wyszukiwania` (SeName) miała pozostać identyczna; zmiana samej nazwy produktu nie wymaga nowego URL.
- Kolumny/tagi cenowe w Excelu: do 2 zł, do 3 zł i do 5 zł. Rzeczywisty zapis tagów do produktów i reguły indeksacji tagów **nie zostały osobno zweryfikowane**. Nie deklarować wdrożenia tagów tylko na podstawie pliku.

## Baseline i pomiar GSC
- Bez płatnego GSC Wizard; źródło = podłączony arkusz:
  https://docs.google.com/spreadsheets/d/11IrPJW-9Y38ZzhMEIhklWge109F8PV5skO4s0nGkgPE/edit
- Zakładka `GSC_DANE`; w audycie 25.10 najświeższa zapisana data = **19.10.2026**. Sprawdzić skrypt/import i jego opóźnienie przed pomiarami.
- Baseline kategorii `/upominki-swiateczne`: 1–19.10.2026: 35 wyświetleń, 2 kliknięcia, średnia pozycja ok. 10,43. Mała próba = bardzo ostrożna interpretacja.
- Nie łączyć sygnałów `papiernia.net.pl opinie` i sztucznie wywołanych SMS-em wyszukiwań brandowych z rozwojem SEO non-brand.
- Kolejna ocena po danych z 01–08.11 i kolejnych dniach (opóźnienie GSC) dla *fraza × URL*; osobno sezonowość i wpływ ostatnich 33 publikacji.

## Related products / cross-sells — ustalenia 25.10.2026
- nopCommerce 4.50.3 wspiera natywnie `Related products` i `Cross-sells`.
- `Related products` jest już aktywne w Papierni: sekcja **Produkty pokrewne** na kartach `/lizaki-swiateczne`, `/magnesy-swiateczne`, `/upominki-firmowe-dla-klientow`, `/herbata-w-fiolce-z-etykieta-na-swieta-upominek-z-logo`.
- Obecny dobór w kilku produktach bardzo podobny (magnesy, karmelki, świeczki, herbata), warto zastąpić rekomendacjami celowymi.
- Admin: `Katalog → Produkty → Edytuj → Produkty powiązane / Related products → Dodaj nowy`; zależnie od tłumaczenia/panelu lokalizacji.
- Zalecenie: 3–4 dobrze dobrane oferty na karcie, nie automatyczne nadmierne kopiowanie 8–10 ofert na każdy produkt; np. 1 alternatywa cenowa, 1 wariant materiałowy, 1 produkt komplementarny i 1 bestseller.
- Rekomendacje nie powinny promować dwóch niemal identycznych stron w sposób, który utrudnia porównanie wariantów; dobierać świadomie.
- `Cross-sells` to inna funkcja (na etapie koszyka), nie zastępuje `Related products`.
- Integracja `Papiernia SEO API` widoczna w repo obsługuje meta/opisy, nie udostępnia obecnie endpointu zarządzania relacjami produktów. Nie deklarować automatycznego wdrożenia relacji bez zmiany i ponownego wdrożenia pluginu.
- SEO: poprawa kontekstowego linkowania wewnętrznego i odkrywania produktów oraz nawigacji, nie gwarancja wzrostu pozycji.
- Źródło: https://docs.nopcommerce.com/en/running-your-store/promotional-tools/cross-sells-and-related-products.html.

### Rekomendowane przykłady powiązań do ustawienia ręcznie
| Produkt | Powiązane 1 | Powiązane 2 | Powiązane 3 |
|---|---|---|---|
| `/lizaki-swiateczne` | `/kolorowe-lizaki-swiateczne-z-personalizowana-etykieta` | `/slodkie-upominki-dla-klientow-na-swieta` | `/ciasteczko-z-wrozba-w-zlotym-pudeleczku-na-boze-narodzenie` |
| `/magnesy-swiateczne` | `/magnes-drobiazg-na-swieta-dla-klientow` | `/notesy-swiateczne-upominki-swiateczne` | `/torebka-papierowa-z-logo-firmy` |
| `/upominki-firmowe-dla-klientow` | `/upominek-swiateczny-dla-klientow` | `/swieczki-dla-pracownikow-upominek-swiateczny-dla-firm` | `/upominki-firmowe-na-boze-narodzenie-herbata-z-logo` |
| `/herbata-w-fiolce-z-etykieta-na-swieta-upominek-z-logo` | `/upominki-firmowe-na-boze-narodzenie-herbata-z-logo` | `/mini-prezenciki-dla-klientek-herbatki-na-boze-narodzenie` | `/zlota-torebka-z-cukierkami-na-swieta-personalizowana-etykieta` |
| `/swiateczne-ciasteczka-z-wrozba` | `/tani-upominek-dla-klientow-na-swieta` | `/ciasteczka-z-wrozba-na-swieta-bozego-narodzenia` | `/ciasteczko-z-wrozba-w-zlotym-pudeleczku-na-boze-narodzenie` |

Status relacji: **propozycje, nie wdrożone przez asystenta**. Obecne relacje sklepu już wyświetlają się publicznie.

## Zasady dalszych prac
- Utrzymywać ten dziennik jako źródło prawdy w projekcie.
- Nie zmieniać krótkich opisów bez wyraźnej potrzeby; szablon `docs/standard-opisu-krotkiego-papiernia.md`.
- Nie usuwać zdjęć; modyfikacja ALT możliwa tylko zgodnie z rzeczywistą zawartością.
- Każdorazowo dziennik: data, URL, nazwa, zmieniona sekcja, status i GSC przed/po.
