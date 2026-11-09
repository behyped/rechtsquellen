# Prüfstand · 10.11.2026

Der freigegebene lokale CY-Vorgänger wurde mit identischem Eingabefingerprint
je einmal als nativer Prozess ausgeführt. Die Anmeldung lief über vorhandene
Abos; kein Provider-API-Key war im Startprozess gesetzt.

| Lauf | Ergebnis |
| --- | --- |
| Codex CLI 0.162.1 | PASS; 134,752 Sekunden; beide Prüfkommandos mit Exit0; 13 Tests OK |
| Claude Code 2.1.321 | PASS; 143,198 Sekunden; beide Prüfkommandos erfolgreich; 13 Tests OK |

Beide lasen die gemeinsame Fachanweisung und unterschieden Fallstichtag,
Originalsprache, Übersetzung und Spiegel. Beide wiesen eine ungeprüfte Aussage
zum 10.11.2026 zurück. Der CY-Prüfstand bleibt 08.11.2026.

Bei Claude wurden zwei Versuche mit angehängter Exitcode-Ausgabe vor der
Ausführung abgelehnt. Danach liefen die zwei exakt erlaubten Kommandos innerhalb
desselben nativen Prozesses. Die Rechte wurden nicht erweitert. Das Bash-Werkzeug
meldete Erfolg ohne eigenes numerisches Exitfeld; der native Gesamtprozess
endete mit Exit0. Diese Abstufung bleibt in den Nachweisen erhalten.

Die vollständigen Modelltranskripte und der getestete interne Fall bleiben
privat. Ihr Eingabefingerprint lautet
`769264a2b72e14e600d3a517028f6d6558b2a67ef5b1acd87481589d754eeb6f`.
Die öffentliche Aufbereitung generalisiert den Fall und ergänzt den ZA-Piloten.
Diese spätere Fassung ist durch die unten dokumentierten Offline-Prüfungen
abgedeckt; weitere native Modellläufe wurden dafür nicht gestartet.

## Grenzen

Ein Zitatvorkommen auf einer PDF-Seite beweist noch nicht die kuratierte
Absatzzuordnung oder eine rechtliche Schlussfolgerung. Kuratierung, Herkunfts-
und Fassungsbewertung bleiben überprüfbare Facharbeit. Der CY-Ausschnitt benennt
nur die Behörde. Die Tests begründen keine allgemeine Rechts- oder Betriebsfreigabe.

## Offline-Prüfungen der öffentlichen Fassung

- Lokaler Arbeitsstand: EU-, CY- und ZA-Fallcheck jeweils Exit0; 24 Tests bestanden.
- Öffentliche Kopie ohne private Belege: EU-Beispielcheck Exit0; 22 Tests bestanden,
  zwei lokale Länder-Integrationsprüfungen ausdrücklich SKIP.
- Fehlender CY-Beleg in der öffentlichen Kopie: erwarteter Exit1 mit Dateilücke.
- Griechische Metadatensuche erfolgreich; Länderfilter und Datumsgrenze getestet.
- Beide nativen Skillverweise samt Datenvertrag in der frischen Kopie bytegleich.
- Skill-Validator: 32 PASS, 3 strukturelle SKIP, 0 FAIL. Die vier verfassten
  Verhaltensszenarien sind Spezifikationen, keine vier ausgeführten Modelltests.
- Kein unabhängiger `skills-ref`-Validator installiert; dessen Abnahme bleibt offen.

[Maschinenlesbarer Prüfbericht](evidence/2026-11-10/validation.json).

