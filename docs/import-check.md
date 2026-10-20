# Gemeinsamer Import-Prüflauf – V0.0.10

`source-import-check` verbindet Studiengangsnavigation, ausdrücklich ausgewählte
Wochen und eine begrenzte Detailstichprobe in derselben HTTP-Sitzung.
Das Ergebnis ist ein bereinigter Prüfbericht, kein veröffentlichter Archivstand.

## Ablauf

1. Prüfzeitraum, ISO-Wochen, Semester und lokale Kennungen vor dem Abruf validieren.
2. Studiengang suchen, exakten Treffer wählen und Planantwort laden.
3. Ausgewählte Wochen gegen den unabhängig vorgegebenen Zeitraum prüfen.
4. Detailverweise aus passenden Wochenantworten zusammenführen. Gleiches
   absolutes Ziel wird auch beim Auftreten in mehreren Wochen nur einmal abgerufen.
5. Bei ungeklärten/fehlerhaften Wochen keine Detailstichprobe starten.
6. Andernfalls höchstens die ausdrücklich gewählte Anzahl von Details prüfen.
7. Lauf-ID, UTC-Zeitstempel, Anwendungsversion, Status und offene Punkte ausgeben.

Fehlende Wochen schließen eine begrenzte Detailstichprobe nicht aus, verhindern
aber jede Vollständigkeitsmeldung. Ein Abruf-/Parserfehler ergibt einen
fehlgeschlagenen Bericht. Nach einem Detailfehler werden keine zuvor gelesenen
Details dieser Stichprobe als erfolgreiches Teilergebnis ausgegeben.

## Manueller Aufruf

Nach Veröffentlichung und Installation von V0.0.10, mit gesetztem `LSF_BASE_URL`:

```bash
python -m flask --app backend source-import-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)" \
  --semester "WiSe 2026/27" \
  --study-key DEMO-STUDIUM --regulations-key DEMO-PO \
  --start 2026-08-31 --end 2027-02-28 \
  --week 2026-W43 --week 2026-W44 --limit 2 --json
```

Die Auswahl ist ein Beispiel mit fiktiven Platzhaltern. Suchtext, exakter
Treffertitel, erwartetes Semester, Zeitraum und Wochen müssen zur gewünschten
Prüfung passen. Die lokalen Kennungen dürfen keine Quelladresse enthalten.
Für den LXC den [systemd-run-Aufbau](source-check.md) verwenden und den
abschließenden Flask-Unterbefehl samt Argumenten ersetzen.

`--json` gibt ausschließlich den strukturierten Bericht aus. Ohne diesen
Schalter erscheint eine kurze Textzusammenfassung. Das Programm speichert keine
Dateien und verändert keine Archivdaten. Ein fehlender oder ungültiger
Laufzeitparameter wird vor dem Prüflauf als CLI-Fehler gemeldet.

## Berichtsvertrag

`schema_version=2` enthält nur ausdrücklich erlaubte Metadaten:

- Lauf-ID, Anwendungsversion, Beginn und Ende in UTC.
- Prüfzeitraum, angeforderte/geprüfte/fehlende und ungeklärte Wochen.
- Anzahl bekannter Detailziele, erfolgreich geprüfter und noch ungeprüfter Details.
- Zahl der Details mit offenen Normalisierungsfragen.
- Status, letzte Phase und maschinenlesbare offene Punkte.

Keine Quelladressen, Formulardaten, Cookies, Hashes der Detailziele, Titel,
Lehrpersonen, Räume oder Kalendervorschauen werden serialisiert. Die Anzahlen
beziehen sich nur auf bereits untersuchte Wochen, nicht auf das gesamte Semester.

| Wert | Bedeutung |
| --- | --- |
| `needs_review` | Prüflauf hat weiterhin offene fachliche oder technische Voraussetzungen |
| `failed` | Navigation, Wochenprüfung oder Detailprüfung ist fehlgeschlagen |
| `missing_weeks` | Erwartete Wochen nicht geprüft |
| `weeks_require_review` | Wochenantwort ungeklärt oder fehlerhaft |
| `unchecked_details` | Bekannte Detailziele nicht vollständig geprüft |
| `normalization_requires_review` | Normalisierung oder ihre Prüfhinweise sind ungeklärt |
| `source_identity_unverified` | Dauerhafte Quellidentität noch nicht belegt |
| `semester_content_unverified` | Inhaltliche Semester-Vollständigkeit noch nicht belegt |

Die Phasen `navigation`, `weeks`, `details` und `finished` zeigen, wie weit
der Prüflauf gelangt ist. Ein Fehler kann zusätzlich einen phasenbezogenen
Code wie `details_failed` erzeugen.

`complete` und `published` bleiben immer `false`. Deshalb endet der neue Befehl
auch nach einem technisch erfolgreichen Prüflauf mit Status **1**. Das ist
beabsichtigt: Ein Scheduler darf ihn noch nicht als erfolgreiche Sicherung
interpretieren. Bei `--json` bleibt auch der Bericht eines erwarteten
Quellfehlers maschinell lesbar; Eingabe-/Konfigurationsfehler vor Laufbeginn
liefern stattdessen eine bereinigte CLI-Fehlermeldung.

## Nachweis und nächste Voraussetzungen

178 lokale Tests bestehen. Die Integration wurde zusätzlich am 2026-10-20 live
für KW 43/2026 und KW 44/2026 geprüft: beide Wochen strukturell passend,
51 unterschiedliche Detailziele aus beiden Wochen, zwei Details geprüft.
24 Wochen und 49 Detailziele bleiben ungeprüft. Zehn HTTP-Anfragen einschließlich
Navigation; keine Rohseiten oder Quelladressen gespeichert.

Die Aktivierung der konfigurierten Quellidentität, Sonderfälle, Wochenenden und der vollständige
Semesterumfang bleiben offen. Erst nach deren Prüfung kann eine sichere
Archivveröffentlichung folgen. Website und Archivdaten bleiben unverändert;
die Startseite übernimmt lediglich die neue Version im Footer.

## Ergänzung V0.0.12

Mit beiden lokalen Identitätseinstellungen werden Sitzungsvarianten derselben Kennung zusammengeführt. Der Bericht ergänzt `identity_mode` (`run` oder `configured`). Bei konfigurierter Kennung bleibt `study_context_unverified` als eigener Blocker erhalten. Details zur Konfiguration und ihren Grenzen: [Veranstaltungskennungen](source-identity.md).
