# Rechtsquellen · Cyprus / EU / South Africa

Offene Quellenkarten, Agentenanweisungen und ein lokaler Zitatprüfer für
Rechtsrecherche. Der Pilot verbindet eine genaue Fundstelle mit Sprache,
Fassung, Stichtag, Original-URL, tatsächlichem Abrufhost und Dateihash.

Der Einstieg funktioniert in Codex und Claude Code über `AGENTS.md` bzw.
`CLAUDE.md`. Eigene Plattform, Modell-API und Vektordatenbank sind nicht erforderlich.
Die Beispieldaten sind synthetisch. Der Prüfer ersetzt keine fachliche Rechtsprüfung.

## In einer frischen Kopie starten

Python 3.10+ und Poppler (`pdftotext`) installieren. Dann im Repo-Stamm:

```sh
python3 scripts/source_context.py --jurisdiction CY --query Datenschutz --as-of 2026-11-08
python3 scripts/source_context.py --jurisdiction CY --query 'προσωπικά δεδομένα'
python3 scripts/check_case.py cases/eu-web-inquiry.json
python3 -m unittest discover -s tests -v
```

Der EU-Beispielcheck funktioniert offline mit den beigefügten EUR-Lex-Belegen.
Die Tests prüfen unter anderem falsche Fassungen, veraltete Stichtage, erfundene
Zitate, manipulierte Dateien und Pfade außerhalb der Nachweisablage.

| Bestand | Umfang und Grenze |
| --- | --- |
| [CY + EU](sources/cy-eu.json) | Behördenwege, griechisches Gesetz 125(I)/2018, Änderung 26(I)/2022 und getrennte englische Übersetzung; zwei eng belegte Fundstellen bis 08.11.2026 |
| [Südafrika](sources/za.json) | Lokaler POPIA-Pilot zu s.18(1)(b), Originalamtsblatt und gesonderte Inkraftsetzung; kein vollständiger POPIA-Check |
| [Sprach- und Kontextablauf](docs/countries/CY.md) | Griechische Originale, englische Hilfstexte, Schreibvarianten, Absatzbezug und unklare Übersetzungen |
| [Vergleich bestehender Projekte](docs/RESEARCH.md) | Klotzkette, EUR-Lex-MCP, Legalize, Lawgent und aktueller Ausfall des Ansvar-CY-Pakets |

## Gesetze sichern und aktuell halten

[Der Arbeitsablauf](docs/monitoring/WORKSPACE.md) führt zur lokalen Bibliothek und
zum einmaligen Änderungscheck. Der ZA-Startbestand umfasst sechs Originalgesetze
und sechs amtliche Übersichtsseiten. Alte Dateien und Abrufquittungen bleiben
versioniert erhalten; ein Inhaltswechsel erzeugt einen prüfbaren Befund.
Projektinteressen können privat angebunden werden. Der gleiche JSON-Prozess lässt
sich im vorhandenen OpenClaw-Monitor verwenden; ein Zeitplan ist nicht installiert.

```sh
python3 scripts/watch_sources.py check
python3 scripts/watch_sources.py status
```

## Mit Agenten arbeiten

1 Skill: [Rechtsquellen-Triage](skills/rechtsquellen-triage/SKILL.md).
Die projektlokalen `.agents/skills/`- und `.claude/skills/`-Verweise zeigen auf
exakt denselben Ordner. Falls ein Checkout keine Symlinks unterstützt, führt
`AGENTS.md` weiterhin direkt zur Fachanweisung.

Beispielauftrag: „Prüfe `cases/cy-web-inquiry.json` am angegebenen Stichtag.
Lies den passenden Länderhinweis. Nenne fehlende Belege und belege jede Aussage
mit der tatsächlichen Prüfausgabe.“

`source_context.py` durchsucht nur kuratierte Metadaten und Suchbegriffe. Es lädt
höchstens die ausgewählten Quellenkarten. Es ist keine Volltextsuche im gesamten
zyprischen Recht. Bei einem späteren Stichtag zeigt es eine offene Aktualisierung.

## Lokale CY- und ZA-Belege

```sh
python3 scripts/check_case.py cases/cy-web-inquiry.json
python3 scripts/check_case.py cases/za-web-inquiry.json --catalog sources/za.json
```

Die CY-/ZA-Rohdateien werden mit diesem Repository **nicht verteilt**. Die
[Manifeste](docs/evidence/catalog-manifest.json) benennen URL, ursprüngliche
Abrufzeit und erwarteten Hash. Beschaffe fehlende Dateien unter den Bedingungen
der jeweiligen Quelle. Eine rechtmäßig vorhandene Datei kann mit
`python3 scripts/import_evidence.py --help` hashgeprüft übernommen werden.
Der Import ruft kein Netz auf und ändert den belegten Rechtsstand nicht.

## Rechte und Beitrag

Eigener Code und eigene Anweisungen: [MIT](LICENSE). Fremde Gesetzestexte und
Übersetzungen behalten ihre jeweiligen Rechte: [DATA-RIGHTS.md](DATA-RIGHTS.md).
Aus der Softwarelizenz eines Rechtsagenten folgt keine Lizenz für seinen Bestand.
[CONTRIBUTING.md](CONTRIBUTING.md) beschreibt Quellenbeiträge und Prüfungen.

Der CY-Vorgänger wurde am 10.11.2026 lokal je einmal in Codex und Claude Code
geprüft: beide technischen Musterläufe bestanden, jeweils 13 Tests.
Die nachfolgende öffentliche Aufbereitung und der ZA-Ausbau haben eigene
Offline-Prüfungen; sie wurden nicht als weitere native Modellläufe ausgegeben.
[Prüfstand](docs/VALIDATION.md).
