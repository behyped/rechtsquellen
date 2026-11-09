# Zypern: Sprache, Fassung und Kontext

Beginne mit Rechtsgebiet, Rolle und Fallstichtag. Sitz, Zielmarkt und zuständige
Aufsicht können auseinanderfallen. Eine Gesellschaft in Zypern begründet für
sich noch keine Antwort auf eine grenzüberschreitende Rechtsfrage.

## Quellen schrittweise laden

1. `source_context.py --jurisdiction CY --query ...` liefert passende Quellenkarten.
   Suche bei Bedarf griechisch und englisch. Gesetzesnummern wie `125(I)/2018`
   bleiben stabile Anker; ein englischer Titel allein ist kein eindeutiger Schlüssel.
2. Lade den ausgewählten Originaldatensatz, dessen konkrete Fundstelle und
   Änderungsbelege. Öffne angrenzende Absätze, Definitionen und Ausnahmen für
   die rechtliche Auslegung. Der kurze Suchauszug allein trägt diese nicht.
3. Lade eine englische Verständnishilfe nur bei Bedarf. Halte Originalsprache,
   Übersetzer/Behörde, Status und zugehörige Textfassung ausdrücklich fest.
4. Zitiere das Original. Füge eine eigene Arbeitsübersetzung getrennt hinzu,
   falls sie zum Verständnis nötig ist. Bei Mehrdeutigkeit bewahre die griechische
   Formulierung und formuliere die offene Frage für die fachliche Prüfung.

## Konkrete Fallstricke

- Der Datenschutzkommissar bezeichnet die englische Fassung von 125(I)/2018
  als inoffizielle Übersetzung. Ein `.gov.cy`-Host macht sie nicht verbindlich.
  Ihr Abruf war blockiert; der Katalog behauptet keine gelesene Übersetzung.
- CyLaw ist ein sekundärer Zugang zu einem amtlichen Faksimile. Normgeber,
  Amtsblatt-Herausgeber und Downloadhost getrennt erfassen. Die Datei wurde
  bisher nicht mit einem erreichbaren GPO-Original abgeglichen.
- Die Änderung 26(I)/2022 betrifft im geprüften Beleg Art.2 und Art.3. Ein
  Änderungsdatum ersetzt nicht automatisch den Wortlaut jeder Vorschrift.
- Das Pilotzitat aus Art.19(1) umfasst nur die Amtsbezeichnung. Es belegt weder
  den gesamten Bestellungsmechanismus noch die konkrete Aufsichtszuständigkeit.
- Historische englische Urteile und neuere griechische Urteile benötigen
  unterschiedliche Suchbegriffe. Der [CoE-Bericht von Juni 2024, S.14](https://rm.coe.int/ai-summarisation-decisions-greek-testing-methodology/1680af6154)
  beschreibt den Sprachwechsel des Supreme Court Ende 1989. Das ist ein
  Suchhinweis; historische Modell- und Tokenkosten des Berichts sind keine
  aktuellen Leistungswerte.
- HTML kann eine griechische Legacy-Zeichenkodierung deklarieren. Dekodierung
  nach Content-Type/Meta prüfen. OCR, Unicode-Normalisierung und Übersetzung
  als Ableitungen speichern; Originalbytes und Originalzitat erhalten.

Die Metadatensuche ignoriert Akzente und Großschreibung. Der Zitatprüfer verändert
den Wortlaut nicht; er normalisiert lediglich Leerraum beim PDF-Abgleich.
Das Register ist ein Pilot, kein vollständiges zyprisches Rechtsverzeichnis.
