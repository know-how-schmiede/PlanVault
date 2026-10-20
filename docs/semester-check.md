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
