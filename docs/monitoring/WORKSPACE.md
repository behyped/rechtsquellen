# Gesetze sammeln und Änderungen prüfen

Dies ist der gemeinsame Arbeitsort für Zypern, EU und Südafrika. Die öffentliche
Sammlung enthält Quelladressen, Metadaten und Werkzeuge. Lokale Gesetzeskopien,
Projektzuordnungen und Review-Befunde liegen unter `private/`.

## Südafrika-Bibliothek

[Quellenliste](../../monitoring/za.json): sechs Originalgesetze und ihre sechs
amtlichen Übersichtsseiten. POPIA, PAIA, Companies Act, Consumer Protection Act,
Electronic Communications and Transactions Act und Cannabis for Private Purposes
Act sind als Startbestand erfasst. [Abrufmanifest](../evidence/za-library-manifest.json).

Nach einem lokalen Lauf führt `private/monitoring/za/LIBRARY.md` zu den gespeicherten
Dateien mit verständlichen Dateinamen. Die Bytes liegen einmal je SHA-256 unter
`objects/`. `captures/` hält jede Abrufquittung, `runs/` die vollständigen verfügbaren
curl-Metadaten, bereinigten Header, Fehler und Laufberichte. Bestehende Fassungen
bleiben erhalten. Die Datumsspalte ist die Abrufzeit, nicht die rechtliche Gültigkeit.

Die sechs Originalveröffentlichungen sind **keine aktuellen konsolidierten Fassungen**.
Die Indexseiten nennen teilweise spätere Änderungen. Der Cannabis-Bestand allein
beantwortet insbesondere keine Frage zur Zulässigkeit eines konkreten Betriebs.
Kommunales Recht, Arbeitsrecht, Steuern, Arzneimittelrecht und sämtliche neuen
Amtsblätter sind durch diese begrenzte Liste nicht abgedeckt.

## Einmal aktualisieren

Python 3.10+, `curl`; für den Zitatprüfer zusätzlich Poppler. Vom Repo-Stamm:

```sh
python3 scripts/watch_sources.py check
python3 scripts/watch_sources.py status
```

Einzelne Quelle: `--source za-companies-index`. Mehrere `--source` sind möglich.
`--profiles monitoring/projects.example.json` ergänzt synthetische Projektinteressen.
Echte Zuordnungen gehören in eine eigene Datei unter `private/monitoring/`, mit
Verweisen auf die bestehenden Projekt- und Entitätsregister. Die beigefügte
Beispieldatei enthält keine echten Firmen oder Kundenakten.

`check` läuft einmal und endet. Höchstens 16 konfigurierte URLs, 6 MB je Antwort,
20 Sekunden je HTTP-Schritt, drei geprüfte Weiterleitungen, insgesamt 240 Sekunden
Netzbudget. Keine automatischen Wiederholungen, Modelle, kostenpflichtigen APIs,
Meldungen oder eingebauten Zeitpläne. Nur die im Skript ausdrücklich erlaubten
amtlichen HTTPS-Hosts können abgerufen werden. Neue Hosts werden im Code geprüft.

| Ergebnis | Bedeutung |
| --- | --- |
| `baseline` | Erster gespeicherter Quellenstand; keine erkannte Rechtsänderung |
| `unchanged` | PDF-Bytes bzw. normalisierter Artikel samt Links unverändert |
| `changed` | Neuer Inhalt; genau ein Befund für Quellen-ID + Vergleichshash |
| `known_version_returned` | Eine bereits gespeicherte frühere Version ist wieder da; sichtbar, kein doppelter Befund |
| `fetch_error` | Fehler/unerwarteter Inhalt; letzter erfolgreicher Stand bleibt erhalten |

Exit 0: technische Prüfung abgeschlossen. Exit 2: mindestens ein Quellenfehler;
bei `status` auch überfällige Quelle (älter als sieben Tage oder noch nie erfasst).
Exit 1: ungültige Eingabe oder lokaler Fehler. Exit 0 ist keine juristische Freigabe.

## Neue Quellen und Fassungen einarbeiten

1. Quelle in `sources/za.json` beschreiben und bei regelmäßigem Bedarf in
   `monitoring/za.json` aufnehmen. Original, amtlicher Index, Änderungsgesetz,
   Inkraftsetzung und Übersetzung getrennt benennen. Bestehende ID beibehalten,
   solange sie dasselbe Dokument bezeichnet; eine andere Quelle erhält eine neue ID.
2. Rechtskonform beschaffte Altbelege mit vorhandener URL, ursprünglicher UTC-Zeit,
   Bytes und Hash übernehmen:
   `python3 scripts/watch_sources.py seed --source QUELLEN-ID --capture BELEG.json`.
   Das Beleg-JSON verweist auf eine Datei unter `private/evidence/` und benutzt
   dieselben Felder wie das bestehende ZA-Manifest. Importzeit und Abrufzeit bleiben getrennt.
3. Änderungen im Original lesen. Artikel-/PDF-Vergleiche liefern einen Anlass zur
   Prüfung; sie erkennen nicht selbst, welche Norm gilt. Neu verlinkte Dokumente
   werden absichtlich nicht automatisch verfolgt. Ergänzungen, Inkraftsetzung,
   Übergänge und betroffene Absätze gezielt belegen.
4. Prüffrage am bestehenden Fachprojekt/Anwaltslog weiterführen. Befund-ID und
   Quellenhash verlinken, Status wie Entwurf/beschlossen/in Kraft, Frist und
   tatsächliche Betroffenheit fachlich ergänzen. Offene Tatsachen offen lassen.
5. Erst nach dieser Prüfung die kuratierten Fassungs-/Zitatdaten aktualisieren und
   `check_case.py` ausführen. Ein erfolgreicher Download verändert niemals
   `checked_through`, `applies_from` oder die öffentliche Datenlizenz.

Die Bibliothek und der Monitor verändern keine Projektaufgaben. Ein neuer Treffer
ist ein Review-Artefakt mit Verweisen auf den bestehenden Auftrag. Neue Projekt-
Interessen lassen sich mit `status --profiles DATEI` gegen alle ausgewählten
Quellen anzeigen; gespeicherte Befunde behalten ihre damaligen Zuordnungsnachweise.

## OpenClaw oder anderer Scheduler

Der Anschluss ist ein gewöhnlicher Prozessaufruf, unabhängig vom Harness:
`check --profiles <private-profile>` liefert JSON und speichert das Ergebnis.
Ein vorhandener Monitor kann neue `findings/*.json` anhand ihrer stabilen ID lesen.
Die Regelprüfung liefert **mögliche** Projektbezüge nach Land und Themeninteresse,
keine abschließende rechtliche Bewertung. Fehlt eine Zuordnung, bleibt der Befund
als unzugeordnet zur Quellenprüfung verfügbar.

Für OpenClaw wird der vorhandene A13-Ablauf verwendet. Dieses Repo installiert
keinen zweiten Scheduler. Vor einem Dauerbetrieb den Repo-Stand, privaten Arbeitsort,
Profilzugriff und den einen vorhandenen Wochenlauf am ausführenden Rechner prüfen.
Ein separater Health-Check muss `status` lesen, damit ausbleibende Läufe sichtbar
werden. Zeitplan, Reader und konkrete Benachrichtigungsroute gehören in dessen
Betriebskonfiguration. Modellbudget des Quellenchecks: null; eine fachliche
Bewertung neuer Funde benötigt ihren eigenen begrenzten Auftrag.

Nachgewiesen sind lokale Ablage, zehn echte Erstabrufe, zwei beleggebundene Importe
und kontrollierte Änderungs-/Dubletten-/Fehlerprüfungen. Eine M1-Installation,
laufender A13-Zeitplan und eine zugestellte Meldung werden damit nicht behauptet.
