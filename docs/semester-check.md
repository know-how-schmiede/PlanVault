# Semesteransichten prüfen – V0.0.13

`source-semester-check` untersucht zusätzlich zur Wochenstichprobe zwei
ausdrücklich ausgewählte Ansichten: die gesamte Semesteransicht und die
Semesteransicht für Block-/Einzeltermine. Dies ist eine Bestandsaufnahme der
Detailverweise; die Detailseiten werden dabei noch nicht abgerufen.

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
eine kurze Zusammenfassung. Es werden höchstens zwölf HTTP-Anfragen einschließlich
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

Der eigene Berichtsvertrag `schema_version=1` enthält Anwendungsversion, Status,
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
