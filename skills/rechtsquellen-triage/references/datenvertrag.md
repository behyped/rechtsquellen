# Vertrag für Rechtsquellen und Fälle

Die drei JSON-Dateien verwenden `schema_version: 1`. Die Dateien sind lesbare
Arbeitsgrundlage für beide CLI-Harnesses. Der lokale Check verwendet dieselben
Dateien für beide.

| Ebene | Pflichtangaben für den Pilot |
| --- | --- |
| Rechtsträger und Fall | Stabile Fall-, Rechtsträger- und Projekt-IDs (Atlas optional), Zielmarkt, Fallstichtag, belegte Sachverhaltsmerkmale, Annahmen, offene Tatsachen und Freigabestatus |
| Quelle | stabile ID, Jurisdiktion, zuständiger Herausgeber, Dokumenttyp, Status des Herausgebers und des Zugangshosts, Sprache, Publikationsdatum und Fundstelle, Original- und Abruf-URL, Datenlizenz mit Beleg oder offene Rechte |
| Fassungsbeleg | eindeutige ID, Inkrafttreten, Anwendungsbeginn der zitierten Vorschrift, gegebenenfalls exklusives Anwendungsende, Prüfdatum, Nachweis-IDs und kurzer Prüfvermerk über Berichtigungen und Änderungen |
| Fundstelle | genaue Normposition, amtliche Seitenzählung und PDF-Seite, kurzer wortgetreuer Auszug, Hash-verknüpfter Abruf |
| Abrufmanifest | URL, UTC, Methode und Parameter, HTTP-/Toolstatus, Umfang, Dateipfad, Format, Bytes, SHA-256, Erfassungsart und bekannte Lücken |

Ein Behördeneinstieg oder ein Registertreffer hat bei Bedarf `null` für
Publikationsdatum und Fassung. Eine zitierbare Norm benötigt positive Belege.
Eine amtliche Publikation auf einem Sekundärhost behält ihren amtlichen
Herausgeber und weist den Spiegel als Zugang getrennt aus. Eine Übersetzung
oder Konsolidierung erhält ihren eigenen Datensatz. Der Versionsbeleg kann
amtliche oder sekundäre Hilfsquellen enthalten und muss deren Grenzen ausweisen.

`checked_through` ist der letzte geprüfte Fallstichtag der konkreten
Fundstelle. Ein unbekanntes Ende ist `null`. Die Kombination erlaubt Zitate
nur bis zum dokumentierten Prüftag. Ergänze spätere Fassungen als eigene
Datensätze. Eine Änderung in einem anderen Artikel führt nicht automatisch
zu einer neuen Textfassung des zitierten Absatzes. Prüfe den Änderungstext.

Der Prüfer setzt ein kuratiertes Quellenregister voraus. Er prüft die
Zuordnung von Zitat und Fassung, die Datumsgrenze, die Hashes der Rohbelege
und das Zitat auf der angegebenen PDF-Seite. Die juristische Herleitung des
Zeitraums und die Subsumtion werden im Fall und durch fachliche Prüfung belegt.
Das Manifest bindet den Dateistand. Ein SHA-256 allein bestätigt weder
Herkunft noch Geltung.
