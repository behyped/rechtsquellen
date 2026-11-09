# Vergleich und Übernahmeentscheidungen · 10.11.2026

Der aktuelle Zusatzvergleich verwendet Primärquellen der jeweiligen Projekte.
Die älteren drei Referenzen wurden am 08.11.2026 direkt gelesen. Das ist keine
behauptete Funktionsabnahme ihrer kompletten Laufzeit.

| Quelle | Geprüfter Stand | Verwendeter Ansatz und Grenze |
| --- | --- | --- |
| [Klotzkette](https://github.com/Klotzkette/claude-fuer-deutsches-recht) | 08.11., Commit `47bd7e9a47364fd47b03b54d6ed2d08c9f282329`; README und Apache-/MIT-Dateien | Fachrouting und genaue Fundstellen. Deutscher Rechtsbestand wird nicht auf CY übertragen. Kein Plugin-Code kopiert. |
| [EUR-Lex MCP](https://github.com/cyanheads/eur-lex-mcp-server) | 08.11., Commit `708121c88405ed6698489de95a652fbc65816a4a`; Apache-2.0 | Stabile CELEX/ELI-Verweise und Fassungsketten. Kann später Transport liefern; bestehender Offline-Prüfer bleibt ohne Server nutzbar. |
| [Legalize](https://github.com/legalize-dev/legalize) | 08.11., Commit `abfba3a3c60f64aac3631225705b6ba32fc02965`; MIT für Software | Rechtsstand nach Datum und nachvollziehbare Änderungshistorie. Datenrechte jeweils gesondert. |
| [Lawgent](https://github.com/WenzhuoXu/lawgent) | 10.11., README, MIT-Lizenz, Commit `17c39bc80316c2ee435a95a63e4c7f02b52c209b` | Länder-/Themenkontext bei Bedarf laden und Zitate gegen Quelldokumente prüfen. Das README sagt ausdrücklich, dass `enable_cite_check` im ausgelieferten Setup ausgeschaltet ist. Kein belegter CY-/ZA-Konnektor und kein nachgewiesener Vorteil im eigenen Vergleichstest. |
| [Ansvar CY-Paket](https://www.npmjs.com/package/@ansvar/cypriot-law-mcp) | 10.11.: npm-Metadaten und [offizielle MCP-Registry](https://registry.modelcontextprotocol.io/v0.1/servers/eu.ansvar%2Fcypriot-law-mcp/versions/latest) | Registrystatus `deprecated`; Betreiber verweist auf authentifizierten Gateway und abgeschaltete Alt-Hosts. GitHub-Metadatenabruf des verlinkten Repos liefert 404. Keine Installation oder Übernahme als funktionierende offene Grundlage. |

Das praktikable Ergebnis ist ein kleiner dateibasierter Quellenkern:
Länderfilter, mehrsprachige Metadaten, genaue Belegprüfung und begrenzte
Kontextauswahl. Er lässt sich im bestehenden Codex-/Claude-Workflow verwenden.
Ein zusätzlicher Modell-Harness oder lokaler Embedding-Stack wäre für diesen
kleinen Bestand derzeit unbelegt. Die Bezeichnung „europagesetz“ konnte im
früheren Vergleich keinem eindeutigen Projekt zugeordnet werden.

## Was tatsächlich im Agentenkontext liegt

`AGENTS.md` führt zur gemeinsamen Fachanweisung. `CLAUDE.md` importiert sie.
Die beiden projektlokalen Skillverweise zeigen auf dieselben Dateien. Erst bei
Bedarf kommen Länderhinweis, Quellenkarte, konkrete Fundstelle und zugehörige
Änderungsbelege hinzu. Kunden- oder Unternehmensregister sind keine Voraussetzung
für das öffentliche Projekt; ein Fachprojekt kann seine vorhandenen IDs mitführen.

Die Metadatensuche lässt griechische Akzente für die Suche weg. Das gespeicherte
Zitat bleibt im Original. Englische Arbeitshilfen erhalten eigene Quellen-IDs
und einen Übersetzungsstatus. Seiten-/Absatzkontext und Ausnahmevorschriften
werden für die Auslegung nachgeladen, statt aus einem Suchfragment zu folgern.

Der [CoE-Bericht von Juni2024](https://rm.coe.int/ai-summarisation-decisions-greek-testing-methodology/1680af6154)
liefert Hinweise zu griechischen Gerichtsentscheidungen und deren Prüfung.
Seine damaligen Modellvergleiche und Kostenwerte sind historische Ergebnisse.
Die lokale Direktdatei war mit 403 blockiert; die Recherche konnte die
bereitgestellte Web-Textdarstellung lesen. Vollständige Direktdateisicherung
wird daher nicht behauptet.

[CyLaw-Nutzungsbedingungen](https://www.cylaw.org/terms.html) und der
[amtliche Hinweis auf die CY-Urheberrechtsquellen](https://www.intellectualproperty.gov.cy/en/knowledgebase/legislation/the-copyright-and-neighbouring-rights-law)
begründen die vorsichtige Verteilung: Metadaten, eigene Texte und konkret
bezeichnete kurze Zitate; kein aus CyLaw übernommenes öffentliches Korpus.
Die tatsächlichen Regeln stehen in [DATA-RIGHTS.md](../DATA-RIGHTS.md).
