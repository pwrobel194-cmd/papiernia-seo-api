# Ahrefs – dodatkowe H1 (audyt 15.11.2026)

## Zakres i stan wykonania

Odczyt wyłącznie diagnostyczny; nie zmieniano danych na papiernia.net.pl.
Lista Ahrefs: 37 adresów = 27 produktów + kategoria `/kategorie` + 9 stron poradnikowych.
Raport źródłowy: `automation/reports/ahrefs-h1-20261115.json`.
Kontekst źródłowego HTML: `automation/reports/ahrefs-h1-dom-20261115.json`.

- 27/27 produktów: w renderowanym HTML są dwa H1; `FullDescription` oraz `ShortDescription` z odczytu API v3 **nie zawierają H1**. Dodatkowy H1 to `Personalizowane upominki`.
- Potwierdzono na produktach Święta oraz Wesele, że nadmiarowy H1 jest wewnątrz elementu `<div id="quickTab-79"><div class="custom-tab">...`, czyli we wspólnej karcie Nop Quick Tabs. Nie pochodzi z opisu produktu.
- Kategoria `/kategorie`: systemowy H1 `Podziękowania dla Gości` i dodatkowy H1 w `category-description`: `Personalizowane podziękowania dla gości i upominki na każdą okazję`.
- Strona `/poradnik`: systemowy H1 `Poradnik` i dodatkowy H1 w `page-body`: `Pomysły, które pomagają wybrać dobrze.`.
- Pozostałe strony poradnikowe: dwa H1 w renderowanym HTML; jeden adres `/co-napisać-na-podziekowaniu-dla-gosci` nie został odczytany automatycznie ze względu na niezakodowany znak `ć` w URL, ale figuruje na dostarczonej liście Ahrefs.

## Jedna poprawka w panelu (nieobsługiwana przez obecne SEO API)

W nopCommerce 4.50.3:
**Plugins / Nop-Templates → Nop Quick Tabs → Manage Tabs**; wyszukaj wspólną zakładkę odpowiadającą `quickTab-79` (przed zmianą sprawdź przypisania).

W edytorze opisu zakładki znajdź tylko ten nagłówek:

```html
<h1 style="margin: 0; font-size: 28px;">Personalizowane upominki</h1>
```

Zmień wyłącznie znaczniki:

```html
<h2 style="margin: 0; font-size: 28px;">Personalizowane upominki</h2>
```

Nie zmieniaj zawartości zakładek (opinie Google, FAQ, modele graficzne). Nie usuwaj zakładek. Sprawdź przed/po na jednym produkcie Święta i jednym Wesele, następnie uruchom skan Ahrefs.

## Osobne 10 stron

- `/kategorie`: Katalog → Kategorie → opis HTML; zamień **drugi** H1 (wewnątrz `category-description`) na H2, zachowując jego tekst i style; nie ruszaj H1 systemowego.
- `/poradnik` i 8 artykułów: Zarządzanie treścią → Tematy (strony), w HTML zamień dodatkowy H1 wpisany w treści na H2, pozostaw H1 systemowego nagłówka.
- Każdy adres sprawdź przed zapisaniem – nie stosuj masowych regexów na ślepo.

## Granice bezpieczeństwa (ważne dla całego projektu Papiernia)

Nie zmieniać adresów URL, H1 produktów/kategorii, SEO Title/Description, krótkich/pełnych opisów poza konkretnym znacznikiem, zdjęć, ALT, galerii „Modele graficzne”, kategorii/przypisań, cen ani informacji „do samodzielnego złożenia”. Zwłaszcza nie zmieniać strategii SEO Święta w trakcie sezonu. Zmiany H1 w Nop Quick Tabs oraz w Topics **nie są dostępne w SEO API v3**, więc nie pozorować skuteczności poprzez edycję `Product.FullDescription`.
