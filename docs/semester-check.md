# Semesteransichten prüfen – V0.0.17

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

Der eigene Berichtsvertrag `schema_version=4` enthält Anwendungsversion, Status,
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
  --study-key DEMO --regulations-key DEMO-PO --detail-budget 80 --json
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

## Berichtsänderung V0.0.15

Schema 3 ergänzt `normalization_summary` mit `preview_count`, `blocked_count`
und `review_preview_count`. Die ersten beiden Werte ergeben zusammen die Zahl
der geprüften Details. Der dritte Wert ist eine Teilmenge der Vorschauen.
`normalization_review_count` umfasst weiterhin blockierte Details und Vorschauen
mit fachlichen Prüfhinweisen. Bei einem abgebrochenen Detailabruf bleiben sämtliche
Detailzähler null. Die Erweiterung gibt keine Titel, Quellwerte oder Freitexte aus.
## Ergänzung V0.0.17 – Zweite Blockdarstellung und Schema 4

Die bisher als `empty_unverified` gemeldete Zusatzansicht enthielt eine vom
Sammler noch nicht erkannte Blockdarstellung. Beide live geprüften Varianten
werden jetzt mit derselben strengen Prüfung von acht Zeilen, Kopfzeile und genau
einem Detailverweis verarbeitet. Raumlinks bleiben ausgeschlossen. Gemischte
Darstellungen werden nach Quellkennung zusammengeführt; dieselbe Kopfzelle wird
auch dann nur einmal gezählt, wenn sie beide CSS-Klassen trägt.

Die aktuelle Bestandsaufnahme umfasst 162 Blöcke und 66 eindeutige Ziele in der
Semesteransicht sowie 98 Blöcke und 33 Ziele in der Zusatzansicht. Die 33 Ziele
sind bereits in der ersten Ansicht enthalten. Damit wurden zwölf zuvor nicht
erfasste Veranstaltungsziele gefunden. Frühere Angaben über 54 Ziele beziehen
sich auf den damaligen, unvollständigen Sammler.

Schema 4 ergänzt pro Ansicht `block_count` und `visible_weekdays` (Montag = 0,
Sonntag = 6). Letzteres enthält ausschließlich erkannte Tagesüberschriften;
eine leere Liste bedeutet keine beobachteten Überschriften. Selbst sieben
beobachtete Wochentage würden noch keine vollständige Inhaltsprüfung belegen.
Der Live-Test zeigt in beiden Ansichten nur Montag bis Freitag. Wochenenden und
Semester-Vollständigkeit bleiben offen; `complete` und `published` bleiben false.

Für die jetzt 66 Ziele `--detail-budget 80` verwenden. Der Standard bleibt 60,
damit größere Abrufe bewusst gewählt werden müssen. Bei Überschreitung des
Budgets starten keine Detailabrufe. Die Gesamtgrenze von 100 HTTP-Anfragen bleibt
unverändert. Tatsächlich blocklose Ansichten bleiben `empty_unverified`.

**Abschließender Live-Lauf V0.0.17:** 74 HTTP-Anfragen, 66 Details geparst, 64 Vorschauen erzeugt (21 mit fachlichen Prüfhinweisen), zwei neu erfasste Details technisch blockiert. Keine Wochenendtermine in den erzeugten Vorschauen; dies ist kein Nachweis für die Abwesenheit weiterer Wochenendveranstaltungen. Nächster Schritt: die zwei neuen Normalisierungsfälle klären und die verbleibenden Vollständigkeitskriterien absichern.

## V0.0.20 – Wochentagsabgleich (Schema 5)

Der JSON-Bericht enthält zusätzlich `weekday_coverage`. `visible_weekdays` und
`unobserved_weekdays` vergleichen die Überschriften beider Ansichten mit allen
sieben Tagen (Montag = 0). `occurrences_by_weekday` zählt die normalisierten
Termine nach lokalem Datum, nicht nach UTC-Datum. `occurrence_weekdays_outside_views`
zeigt Tage mit Terminen, die in keiner beobachteten Tagesüberschrift vorkommen.

Ohne abgeschlossene Detailprüfung bleibt `details_checked` false und
`blocked_details` null. Null ist nicht mit null blockierten Details zu verwechseln.
Die Terminzähler enthalten ausschließlich Vorschauen; blockierte Details werden
separat gezählt und nicht als leere Termine behandelt. Ein abgebrochener Abruf
liefert keine Teilzählung. Die Werte enthalten keine Namen oder Hinweistexte.

`weekend_coverage_verified` bleibt ausdrücklich false: Weder sieben Überschriften
noch das Fehlen von Wochenendterminen beweisen die vollständige Erfassung.
Auch `complete` und `published` bleiben false. Der nächste notwendige Nachweis
ist weiterhin eine belastbare Erfassung aller Semestertage sowie die Klärung
der offenen Bemerkungen. Der neue Abgleich ist mit fiktiven Daten getestet;
ein vollständiger Live-Semesterlauf wurde für V0.0.20 nicht wiederholt.

## Optionale Web-Vorschau ab V0.0.21

Nur mit --details, --save-preview und konfiguriertem PREVIEW_FILE schreibt der Prüflauf normalisierbare Termine separat als unvollständige Web-Vorschau. Ohne diese Option bleibt der Aufruf unverändert ohne Dateischreibzugriff. Einrichtung, Zugriff und Exitcode erläutert die [Vorschau-Anleitung](preview.md). Keine Archivfreigabe.


## V0.0.23: Ursachen und offene Nachweise (Schema 6)

Den bisherigen `source-semester-check --details ... --json`-Aufruf mit den bereits
lokal eingerichteten Argumenten erneut ausführen. Keine zusätzlichen Abrufe werden
für die Diagnose benötigt. Der Bericht enthält jetzt:

- `review_summary.reason_counts`: Anzahl betroffener Details pro Ursache, einschließlich fachlicher Prüfhinweise erfolgreicher Vorschauen.
- `review_summary.details`: laufbezogene `detail_number`, `blocked` und `reasons`. Die Nummer gilt nur innerhalb dieses Berichts und ist keine dauerhafte Veranstaltungskennung.
- `completeness_review.blockers`: offene Nachweise für Semesteransichten, ungeprüfte Details, Normalisierungsblockaden und fachliche Hinweise. Studiengangszuordnung, Semesterumfang und Wochenendabdeckung bleiben bis zu eigenständiger Verifizierung offen.
- `completeness_review.eligible_for_publication`: weiterhin `false`. Ein technisch vollständig geprüfter bekannter Detailbestand reicht nicht zur Freigabe.

| Ursachencode | Nächste Prüfung |
| --- | --- |
| `unsupported_series_note` | Serienbemerkung lokal mit der Quelle vergleichen; erst nach Beleg eine eng begrenzte Regel ergänzen. |
| `unsupported_execution_note` | Durchführung oder Gruppierung fachlich klären. |
| `unsupported_recurrence` | Unbekannten Rhythmus anhand der Quelle verifizieren. |
| `unsupported_cancellation_format` | Struktur der Ausfallangabe prüfen. |
| `cancellation_outside_series` | Ausfalldatum und zugehörige Serie vergleichen. |
| `ambiguous_local_time` | Termin während der Zeitumstellung prüfen. |
| `invalid_exam_time` / `exam_time_outside_series` | Klausurhinweis und Tabellenzeiten vergleichen. |
| `normalization_requires_review` | Andere ungültige oder bislang nicht eindeutig normalisierbare Angaben prüfen. |

Pro blockiertem Detail wird die erste blockierende Ursache gemeldet. Nach deren
Behebung können weitere Ursachen sichtbar werden. Erfolgreiche Vorschauen führen
alle vorhandenen Prüfcodes auf; ein Detail kann deshalb mehrere Zähler erhöhen.
Die Textausgabe nennt dieselben Ursachenzähler und offenen Vollständigkeitsnachweise.
Ohne `--details` bleiben Ursachenzähler leer und `details_unchecked` bleibt offen.

Berichte enthalten keine Bemerkungstexte, Titel, Lehrpersonen, Räume oder
Quellkennungen. Ungeklärte Originaldaten bleiben ausschließlich im Arbeitsspeicher.
Ein fehlgeschlagener Prüflauf liefert weiterhin keine erfolgreiche Teilstichprobe;
Status und Exitcode sind zusammen mit der Diagnose zu beachten. Exitcode 1,
`complete: false` und `published: false` bleiben unverändert.

Lokal mit fiktiven Grenzfällen geprüft. Kein neuer Live-Import und keine Freigabe
der dokumentierten Einführungsbemerkungen; deren Bedeutung bleibt ungeklärt.


## Live-Nachprüfung V0.0.24

Eine getrennte Untersuchung der WI-Prüfungsordnung 2020 erfasst 21 bekannte
Detailziele. Der bisher blockierende reine Raumhinweis kann jetzt als
prüfpflichtige Annotation normalisiert werden. Dieser Lauf ersetzt weder die
frühere Untersuchung mit 66 Details noch eine Prüfung mit den lokal konfigurierten
dauerhaften Kennungen. Nach der Erweiterung erzeugen alle 21 bekannten Details
insgesamt 309 Vorschautermine; drei Details bleiben fachlich prüfpflichtig.
Laufbezogene Quellkennungen erscheinen zusätzlich als
`source_identity_unverified` in der Vollständigkeitsliste. Vollständigkeit und
Archivfreigabe bleiben gesperrt.
Die Untersuchung hat keine Vorschau-Datei aktualisiert. Konkrete Grenzen und
Abrufzahlen stehen in der [Quellenanalyse](source-analysis.md).


## V0.0.25 – Wiederverwendbare Auswahl und Speicherstatus (Schema 7)

`source-semester-check` unterstützt die Umgebungsvariablen `LSF_STUDY_QUERY`,
`LSF_STUDY_TITLE`, `LSF_SEMESTER`, `LSF_STUDY_KEY` und `LSF_REGULATIONS_KEY` als
Vorgaben für die entsprechenden Optionen. Explizite Optionen haben Vorrang.
Die vertrauliche Laufzeitkonfiguration wird weiterhin vor dem CLI-Aufruf geladen;
es gibt keine automatische Übernahme einer Datei und keinen voreingestellten
Produktionsstudiengang. Fehlende Detailwerte werden vor dem Quellzugriff abgelehnt.

Schema 7 ergänzt `preview_save` mit `requested`, `saved` und `event_count`.
Nur ein erfolgreich abgeschlossener Dateiaustausch setzt `saved` auf true. Bei
Fehlern oder ohne Speicherauftrag ist es false; dies sagt nichts über eine bereits
vorhandene Vorschau-Datei aus. Die bestehenden Archivfelder und Exitcode 1 bleiben
unverändert. Textausgabe und JSON unterscheiden nun zwischen abgeschlossener
Detailprüfung und tatsächlich gespeicherter Web-Vorschau.

Der ursprüngliche MT-Bestand wurde mit 66 Details erneut live geprüft. 65
Vorschauen mit 942 Terminen wurden temporär gespeichert und über Wochen-/Listenansicht
lokal ausgegeben. Ein Einführungsfall bleibt technisch blockiert, 23 Vorschauen
fachlich prüfpflichtig. Nur laufbezogene Quellzuordnung, keine LXC-Aktualisierung.
[Konkrete Einrichtung für den LXC](preview.md#web-vorschau-ab-v0025-mit-wiederverwendbarer-auswahl).
