# Semesteransichten prüfen – V0.0.14

`source-semester-check` untersucht zusätzlich zur Wochenstichprobe zwei
ausdrücklich ausgewählte Ansichten: die gesamte Semesteransicht und die
Semesteransicht für Block-/Einzeltermine. Dies ist eine Bestandsaufnahme der
Detailverweise; ohne die Option `--details` werden keine Detailseiten abgerufen.

## Aufruf

Nach Veröffentlichung und Installation dieser Version die vertrauliche
Laufzeitkonfiguration wie beim [Quelltest](source-check.md) laden.
`LSF_BASE_URL` und beide Einstellungen der [Quellkennung](source-identity.md)
müssen gesetzt sein. Im Anwendungsumfeld ausführen:

```bash
python -m flask --app backend source-semester-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)" --json
```

Die Auswahl ist fiktiv und muss lokal ersetzt werden. Ohne `--json` erscheint
eine kurze Zusammenfassung. Ohne Detailprüfung werden höchstens zwölf HTTP-Anfragen einschließlich
Navigation erlaubt; Wiederholungen sind ausgeschaltet, das bestehende Rate-Limit
bleibt aktiv. Keine Dateien oder Archivdaten werden geschrieben.

## Prüfung und Bericht

- Die Auswahl wird über sichtbare Beschriftungen aufgelöst. Tatsächliche
  Formularnamen und Werte bleiben ausschließlich im Arbeitsspeicher.
- Jede Antwort muss die angeforderte Ansicht ausgewählt haben. Das datierte
  Wochenangebot darf sich während der Prüfung nicht verändern.
- Vorhandene Veranstaltungsblöcke müssen der bereits geprüften Detailstruktur
  entsprechen. Die konfigurierte Kennung ordnet Sitzungsvarianten zusammen.
- Zusätzliche Kennungen der zweiten Ansicht werden gegenüber der ersten gezählt.
  Gleiche Titel allein führen niemals zu einer Zusammenführung.
- Keine erkannten Blöcke ergibt `empty_unverified`, niemals einen bestätigten
  Leerbestand. Auch eine Fehlerseite ohne Blöcke kann damit keine Freigabe erzeugen.
- Bei Struktur- oder Abruffehlern lautet der Bericht `failed`; es wird keine
  erfolgreiche Teilbestandsaufnahme ausgegeben.

Der eigene Berichtsvertrag `schema_version=2` enthält Anwendungsversion, Status,
Ansichtscodes, Anzahl eindeutiger Detailziele und zusätzliche Ziele der zweiten
Ansicht. Der erste `additional_count` ist definitionsgemäß null. URLs,
Kennungen, Titel und andere Quellinhalte werden nicht ausgegeben.
`complete` und `published` sind immer `false`, der Prozessstatus ist **1**.
Konfigurationsfehler vor Beginn liefern eine bereinigte CLI-Fehlermeldung.

## Live-Nachweis und verbleibende Arbeit

Am 2026-10-20 wurde der implementierte Adapter mit acht HTTP-Anfragen geprüft:
54 eindeutige Detailziele in der Semesteransicht; keine erkannten Blöcke in der
Block-/Einzelterminansicht. Das ist mehr als die 51 unterschiedlichen Ziele
der früheren Zwei-Wochen-Stichprobe; die Zahlen stammen aus getrennten Prüfungen.
Die zusätzlichen Ziele sind ein Hinweis auf die Bedeutung der Semesteransicht,
kein Beweis für deren Vollständigkeit.

Die Quelle zeigt weiterhin Montag bis Freitag. Wochenenden, die Semesterauswahl,
die leere Zusatzansicht und sämtliche Veranstaltungsdetails müssen noch
abgesichert werden. Der neue Befehl ersetzt den bisherigen Import-Prüflauf
nicht und erteilt keine Archivfreigabe. Nächster Schritt ist die Zusammenführung
der Semesterziele mit einer begrenzten, vollständigen Detailerfassung und
nachvollziehbarer Prüfung des gewählten Semesters.

## Alle bekannten Details prüfen

Mit `--details` müssen erwartetes Semester, Studiengangs- und Prüfungsordnungskennung
zusätzlich angegeben werden. Beispiel mit ausschließlich fiktiven Auswahlwerten:

```bash
python -m flask --app backend source-semester-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)" \
  --details --semester "WiSe 2026/27" \
  --study-key DEMO --regulations-key DEMO-PO --detail-budget 60 --json
```

Das Detailbudget beträgt standardmäßig 60, zulässig sind 1 bis 100. Es wird vor
jedem Detailabruf gegen die Gesamtzahl eindeutiger Ziele geprüft: kein stilles
Abschneiden auf eine Stichprobe. Insgesamt gilt zusätzlich eine harte Grenze von
100 HTTP-Anfragen inklusive Navigation und Weiterleitungen. Bei ausgeschöpfter
Grenze schlägt der Lauf fehl; Wiederholungen sind ausgeschaltet.

Jede Detailseite muss das angegebene Semester enthalten. Bereits ein Abruf-,
Semester- oder Parserfehler beendet die Prüfung ohne erfolgreiches Teilergebnis.
Nicht unterstützte Normalisierungen werden gezählt und verhindern weiterhin
eine Freigabe. Daten bleiben nur im Arbeitsspeicher.

Schema 2 ergänzt `details_requested`, `checked_details`,
`normalization_review_count` und `known_details_checked`. Letzteres bedeutet
nur, dass alle bekannten Detailseiten den Parser durchlaufen haben. Es bestätigt
weder die Semesterwahl der Übersicht noch Vollständigkeit oder fehlerfreie
Normalisierung. Bei Detailfehlern bleiben Zähler null und das Kennzeichen false;
bereits geprüfte Übersichten dürfen als Diagnose im Bericht verbleiben.
`complete` und `published` bleiben false, Prozessstatus weiterhin 1.

**Live-Prüfung V0.0.14 (2026-10-20):** Alle 54 bekannten Detailziele wurden mit insgesamt 62 HTTP-Anfragen geparst und gegen das erwartete Semester geprüft. 21 Details bleiben wegen Normalisierung oder fachlicher Prüfhinweise offen. Es wurden keine Rohseiten oder vertraulichen Quellwerte gespeichert. Nächster Schritt: diese offenen Normalisierungsfälle gezielt untersuchen und unterstützen; Vollständigkeit der Quelle weiterhin separat nachweisen.
