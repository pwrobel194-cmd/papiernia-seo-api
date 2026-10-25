# Papiernia — OBOWIĄZUJĄCY wzór krótkiego opisu HTML

Ustalony przez właściciela sklepu 25.10.2026. **Stosować do KAŻDEGO nowego produktu, niezależnie od kategorii (Święta, Komunia, Chrzest, Wesele, B2B itd.) i przy poprawianiu krótkich opisów wyłącznie na wyraźne polecenie.** Szablon HTML: [docs/templates/opis_krotki.html](templates/opis_krotki.html).

## Niezmienne zasady układu

- Pierwszy element: `<div style="text-align:center;line-height:1.6;">`. Nie zastępować go listą `<ul>`, tabelą, innym CSS-em ani układem lewostronnym.
- Sekcja 1: wyróżniona nazwa produktu + 1–2 zdania korzyści/zastosowania.
- Potem dokładnie wizualny odstęp `<br>`.
- Sekcja 2: co obejmuje **cena za 1 sztukę**, co może zawierać personalizacja, jeden model na zamówienie.
- Odstęp i separator `<br><hr>`, wyśrodkowany tytuł `Charakterystyka produktu:`, separator `<hr>`.
- Sekcja parametrów: format `<p><strong>Nazwa:</strong> wartość.<br>...` bez wypunktowania. Uwzględnić faktyczną zawartość, wymiary, etykietę, rodzaj/wymiary wstążki lub inne ustalone parametry, modele, minimum zakupowe.
- Separator `<hr><br>`, tytuł `Jak zamówić ten produkt?` i cztery kroki numerowane tekstowo w pojedynczym `<p>`, rozdzielone `<br>`.
- Zamknięcie `</div>`, a **pod nim, poza wyśrodkowaną sekcją**, ważna informacja: `<p><strong>Ważne – samodzielne złożenie:</strong> ...</p>`.
- **Jeżeli produkt nie wymaga samodzielnego złożenia, nie twierdzić, że wymaga** — pominąć blok albo zastąpić potwierdzoną istotną informacją.
- Nie wymyślać składu, materiałów, wymiarów, liczb modeli, ceny ani warunków; brak danych oznaczyć jako do weryfikacji przed publikacją. Nie twierdzić, że modele są dostępne w zakładce, jeśli nie zostały dodane.
- Dla istniejących produktów: nie zmieniać krótkiego opisu przy zwykłym audycie SEO bez wyraźnego zlecenia. Nowe produkty: szablon stosować obowiązkowo.
- Nie zastępować tego wzoru alternatywą podczas następnego dodawania produktów. Paczka wdrożeniowa ma zawsze zawierać krótką wersję w tym formacie i kompletną wersję pełnego opisu oddzielnie.

## Ważne rozróżnienie

Ten standard dotyczy **układu i informacji zakupowych** krótkiego opisu, nie fraz ogólnych SEO kategorii. Produkt ma własną szczegółową frazę, kategoria hub utrzymuje frazy szerokie.
