# Wochen- und Semesteransichten abgleichen – ab V0.0.26

`source-coverage-check` vergleicht die Veranstaltungsziele beider Semesteransichten
mit den Zielen ausdrücklich gewählter Wochen. Ohne `--details` liest er keine
Detailseiten. Ab V0.0.27 ist zusätzlich ein Wochenpräsenzabgleich mit Detailseiten
möglich (siehe unten). Er schreibt weder Archivdaten noch eine Vorschau-Datei. Eine vorhandene
Web-Vorschau bleibt unverändert.

## Im LXC ausführen

Zuerst V0.0.29 auf GitHub veröffentlichen und das bestehende
[Update](install.md#vorhandene-installation-aktualisieren) ausführen. Ein Neustart
allein aktualisiert den Anwendungscode nicht. Die bekannte lokale Konfiguration
für Quelladresse und Veranstaltungskennung wird weiterhin benötigt; siehe
[Quellkennung](source-identity.md). Keine vertraulichen Werte veröffentlichen.

Als root mit den Standardpfaden und dem Standarddienstkonto:

```bash
cd /opt/wi-planarchiv
set -a
. /etc/wi-planarchiv/app.env
set +a
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-coverage-check \
  --query "Wirtschaftsingenieur" \
  --title "BWING MT | Wirtschaftsingenieurwesen / Management und Technik (PO-Version 2024)" \
  --start 2026-08-31 --end 2027-02-28 \
  --all-weeks --week-budget 30 --json
```

Abweichende Installationspfade und Dienstkonten lokal anpassen. Die
Konfigurationsdatei muss vom Administrator gepflegt und vertrauenswürdig sein.
Wenn `LSF_STUDY_QUERY` und `LSF_STUDY_TITLE` bereits exportiert sind, können die
entsprechenden Optionen entfallen. Explizite Optionen haben Vorrang.

Der Zeitraum ist ein bewusst gewählter Prüfauftrag. Er stimmt beim Live-Test mit
den 26 angebotenen Wochen überein, ist aber kein unabhängig bestätigter Nachweis
der fachlich vollständigen Semestergrenzen. Andere Zeiträume ausdrücklich
angeben; das Programm leitet die erwarteten Wochen nicht aus dem Quellmenü ab.

Für eine kleine Stichprobe stattdessen eine oder mehrere Wochen wählen:

```bash
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-coverage-check \
  --query "Wirtschaftsingenieur" \
  --title "BWING MT | Wirtschaftsingenieurwesen / Management und Technik (PO-Version 2024)" \
  --start 2026-08-31 --end 2027-02-28 \
  --week 2026-W43 --week 2026-W44 --week-budget 2 --json
```

Genau eine Auswahlart ist erforderlich: `--all-weeks` oder wiederholtes `--week`.
Doppelte Wochen, Wochen außerhalb des Zeitraums und Budgetüberschreitungen werden
vor dem ersten Quellabruf abgelehnt. Erwartete, nicht angebotene Wochen erscheinen
als nicht verfügbar und bleiben fehlend. Alle erreichbaren angeforderten Wochen
werden innerhalb des Budgets geprüft. Nicht angeforderte Wochen bleiben fehlend.

## Ablauf und Grenzen

1. Studiengang über die bekannte Suche wählen und das datierte Wochenangebot lesen.
2. Semesteransicht und Block-/Einzelterminansicht strukturell prüfen und ihre Ziele vereinigen.
3. Gewählte Wochen seriell abrufen, Auswahl und Tagesdaten prüfen und Ziele sammeln.
4. Ziele anhand der konfigurierten Veranstaltungskennung vergleichen. Unterschiedliche Sitzungslinks derselben Kennung werden zusammengeführt; widersprüchliche Beschriftungen führen zum Abbruch.

Standardbudget sind 30 Wochen, ausdrücklich einstellbar zwischen 1 und 54.
Zusätzlich gilt die harte Grenze von 100 HTTP-Anfragen einschließlich
Weiterleitungen, eine Sekunde Mindestabstand, Timeout und keine Wiederholungen.
Ein Budget garantiert nicht, dass jede Quelle mit vielen Weiterleitungen innerhalb
der HTTP-Grenze erreichbar ist. Bei Grenzüberschreitung schlägt der Lauf fehl.

Ferien-/Tageshinweise und strukturgeprüfte leere Wochen führen im neuen Abgleich
nicht zum Abbruch. Vorhandene Ziele werden auch dort gezählt; deren Status bleibt
`notes_require_review` beziehungsweise `empty_unverified`. Es wird kein freier
Zeitraum bestätigt. Abruf-, Struktur-, Kennungs- oder Zuordnungsfehler stoppen
hingegen weitere Wochenabrufe. Es gibt danach keinen erfolgreichen Teilvergleich.
Das bisherige Verhalten der anderen Wochen- und Importprüfbefehle bleibt bestehen.

## Bereinigter Bericht (eigener Vertrag, ab V0.0.29 Schema 4)

| Feld | Bedeutung |
| --- | --- |
| `requested_weeks` | Explizit gewählte oder alle aus dem angegebenen Zeitraum berechneten ISO-Wochen. |
| `unavailable_weeks` | Angeforderte Wochen, die im Quellmenü fehlen. |
| `checked_weeks` | Wochenstatus und Anzahl beobachteter Ziele je Woche; bei fehlgeschlagener Wochenprüfung ist die Zielanzahl `null`. |
| `missing_weeks` | Wochen des gesamten Prüfzeitraums ohne abgeschlossene Wochenprüfung, auch außerhalb einer Stichprobe. |
| `review_weeks` | Leere oder mit Tageshinweisen versehene Wochen. |
| `failed_weeks` | Durch Abruf- oder Strukturfehler fehlgeschlagene Wochen. |
| `all_requested_weeks_observed` | Alle angeforderten Wochen wurden strukturell gelesen, einschließlich prüfpflichtiger Wochen. |
| `period_weeks_verified` | Alle erwarteten Wochen des Zeitraums wurden ohne fehlende, fehlerhafte oder prüfpflichtige Wochen geprüft. Kein Semester- oder Wochenendnachweis. |
| `comparison_evaluated` | Ein Zielvergleich der beobachteten Wochen wurde berechnet. Ohne beobachtete Wochen oder nach Fehlern bleibt er aus. |
| `comparison_scope` | Immer `observed_weeks`: Der Vergleich betrifft ausschließlich die tatsächlich beobachteten Wochen. |
| `comparison.semester_reference_count` | Unterschiedliche Ziele aus beiden Semesteransichten zusammen. |
| `comparison.week_reference_count` | Unterschiedliche Ziele aus den beobachteten Wochen zusammen. |
| `comparison.shared_reference_count` | In beiden Beständen vorhandene Ziele. |
| `comparison.only_in_weeks` | Laufbezogene Nummern der Ziele, die nur in den beobachteten Wochen vorkommen. |
| `comparison.only_in_semester_views` | Laufbezogene Nummern der Ziele, die in keiner beobachteten Woche vorkommen. Kein Nachweis einer Löschung oder eines Ausfalls. |
| `comparison.reference_sets_equal` | Gleichheit dieser beiden Zielmengen; bei einer Stichprobe kein Nachweis für alle Wochen. |
| `blockers` | Offene Nachweise und erkannte Unterschiede. |

Die Nummern beginnen bei eins, zuerst in der Reihenfolge der vereinigten
Semesterziele, danach für zusätzliche Wochenziele. Sie gelten nur für diesen Lauf,
sind keine dauerhaften Veranstaltungskennungen und sind nicht mit Nummern anderer
Prüfberichte gleichzusetzen. Titel, Räume, Lehrpersonen, Quelladressen,
Quellkennungen und Formularparameter werden nicht ausgegeben.

Bei `status: failed` ist `comparison` null und `comparison_evaluated` false.
Bei einem technisch durchgelaufenen Abgleich bleibt der Status `needs_review`.
`complete`, `published` und `weekend_coverage_verified` bleiben immer false;
der Befehl endet mit **Exitcode 1**. Im Standardmodus werden keine Detailseiten
oder Einzeltermine geprüft. Auch mit `--details` werden keine Uhrzeiten und Räume
mit den Wochenansichten verglichen. Er veröffentlicht und aktualisiert keine Daten
auf der Webseite.

## Live-Nachweis vom 2026-10-21

Die bekannte MT-Auswahl mit Prüfungsordnung 2024 wurde für den oben genannten
Zeitraum über den implementierten Abgleich geprüft: 34 HTTP-Anfragen, beide
Semesteransichten und alle 26 angeforderten Wochen erreicht. Semesteransicht:
66 Ziele; Block-/Einzelterminansicht: 33 Ziele. Vereinigter Wochenbestand:
66 Ziele, alle auch in den Semesteransichten vorhanden. Keine Ziele nur in
Wochenansichten oder nur in Semesteransichten.

Zehn Wochen sind ungeklärt leer: KW 36–40/2026 und KW 4–8/2027. Drei weitere
Wochen, KW 52–53/2026 und KW 1/2027, tragen Tageshinweise; dort wurden 23, null
und 13 Ziele erfasst. 13 Wochen haben Status `ok`. Keine angeforderte Woche fehlt,
kein Abruf-/Strukturfehler. `all_requested_weeks_observed` ist true,
`reference_sets_equal` ist true, `period_weeks_verified` bleibt false.

Dieser Lauf verwendet konfigurierte, zuvor in getrennten Sitzungen geprüfte
Veranstaltungskennungen. Er bestätigt Zielübereinstimmung innerhalb des gewählten
Prüfzeitraums. Der ungeklärte Einführungsfall, Ausfälle, Verlegungen,
Raumwidersprüche, Wochenenden und die fachlichen Semestergrenzen sind damit
nicht gelöst. Keine Detailabrufe, Rohdatenspeicherung, Vorschauaktualisierung
oder Archivfreigabe. Der Live-Test erfolgte aus der Entwicklungsumgebung;
ein eigener Lauf im Ziel-LXC steht für diesen Befehl noch aus.


## V0.0.27 – Detailseiten gegen die Wochenpräsenz prüfen

Ein Veranstaltungsziel kann über das Semester hinweg in beiden Ansichten
vorkommen und trotzdem in einer bestimmten Woche fehlen. Mit `--details` liest
der Abgleich deshalb zusätzlich alle bekannten Ziele aus beiden Semesteransichten
und den beobachteten Wochen einmalig. Jede Detailseite muss zur ausdrücklich
erwarteten Semesterbezeichnung passen. Eine abweichende Semesterbezeichnung,
Abruf- oder Parserfehler verwerfen den gesamten Vergleich dieses Laufs.

### Aufruf im LXC

Nach Veröffentlichung und Update auf V0.0.27 die lokale Konfiguration wie oben
laden und im Installationsverzeichnis als root ausführen:

```bash
runuser -u wi-planarchiv -- env PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m flask --app backend source-coverage-check \
  --query "Wirtschaftsingenieur" \
  --title "BWING MT | Wirtschaftsingenieurwesen / Management und Technik (PO-Version 2024)" \
  --start 2026-08-31 --end 2027-02-28 \
  --all-weeks --week-budget 30 \
  --details --semester "WiSe 2026/27" \
  --study-key "WI-MT" --regulations-key "PO-2024" \
  --detail-budget 80 --json
```

Falls bisher andere opake Studiengangs-/Prüfungsordnungskennungen verwendet wurden,
diese beibehalten. Die fünf Auswahloptionen können wie beim Vorschauimport aus
der exportierten lokalen Konfiguration übernommen werden; explizite Optionen haben
Vorrang. Detailparameter ohne `--details` werden nur als Umgebungs-Vorgaben ignoriert,
als ausdrücklich übergebene Optionen dagegen abgelehnt.

`--detail-budget` erlaubt 1 bis 100 Ziele, Standard 80. Überschreitet der vereinigte
Bestand das Budget, bricht der Lauf vor dem ersten Detailabruf ab. Es wird nicht
stillschweigend nur ein Teilbestand geprüft. Das harte HTTP-Limit bleibt bei
**100 Anfragen für den gesamten Lauf**, einschließlich Navigation und
Weiterleitungen. Der vollständige Live-Lauf benötigte genau 100 Anfragen; bereits
eine zusätzliche Weiterleitung oder ein weiterer Datensatz kann zum Abbruch
führen. Für einen kleineren Prüfauftrag `--all-weeks` durch beispielsweise
`--week 2026-W43 --week 2026-W44` ersetzen. Das Detailbudget und HTTP-Limit bleiben
dabei wirksam; alle bekannten Ziele der Semesteransichten werden dennoch geprüft.

### Was genau verglichen wird

Verglichen wird **eine Veranstaltung pro vollständiger beobachteter Woche**.
Mehrere Termine oder Gruppen derselben Veranstaltung innerhalb einer Woche werden
für diese Prüfung zusammengefasst. Ein passender Wocheneintrag bestätigt deshalb
weder die einzelnen Tage noch Uhrzeiten, Räume oder alle Gruppen. Als erwartete
Präsenz gilt mindestens ein normalisierter Termin von Montag bis Freitag.
Die Zuordnung verwendet das lokale Datum in Europe/Berlin einschließlich korrektem
ISO-Jahr, nicht das UTC-Datum.

- Nicht beobachtete Wochen werden nicht als Wochen ohne Termine behandelt.
- Unvollständige Randwochen des Prüfzeitraums werden separat ausgewiesen und nicht verglichen: Ein sichtbarer Eintrag könnte außerhalb des gewählten Datumsintervalls liegen.
- Samstag-/Sonntagstermine werden gezählt und vom Vergleich der bisher nur Montag bis Freitag darstellenden Wochenansicht ausgenommen. Wochenenden bleiben ungeprüft.
- Blockierte Details werden mit laufbezogener Nummer ausgewiesen, ohne aus ihnen einen leeren Terminbestand abzuleiten.
- Explizite Ausfälle entfernen die entsprechenden erwarteten Termine. Ein dennoch sichtbarer Wocheneintrag mit ausschließlich Ausfallangaben wird separat gemeldet, nicht automatisch als zusätzlicher Termin gewertet.
- Offene Bemerkungen, Raum-/Verlegungshinweise und Tageshinweise bleiben prüfpflichtig. Eine Abweichung ist ein Prüfauftrag, kein bestätigter Ausfall und kein Anlass zur automatischen Terminänderung.

### Zusätzliche Felder im Schema 2

| Feld | Bedeutung |
| --- | --- |
| `details_requested` / `checked_details` | Detailauftrag und Anzahl vollständig abgearbeiteter Details. |
| `normalization_summary` / `review_summary` | Vorschauen, Blockaden und feste Prüfcodes; keine Freitexte. |
| `weekly_presence.scope` | Immer `course_presence_per_full_observed_week`. |
| `weekly_presence.evaluated` | Mindestens eine volle Woche und ein normalisierbares Detail konnten verglichen werden. |
| `weekly_presence.weeks` | Zähler je verglichener Woche mit unverändertem Wochenstatus. |
| `weekly_presence.expected_course_weeks` | Erwartete Kombinationen aus Veranstaltung und Woche für normalisierbare Details. |
| `weekly_presence.observed_course_weeks` | Sichtbare Kombinationen für diese Details und Vergleichswochen. |
| `weekly_presence.matched_course_weeks` | In beiden Mengen vorhandene Kombinationen. |
| `weekly_presence.missing_from_week_view` | Erwartete, aber nicht sichtbare Kombinationen mit Detailnummer, ISO-Woche und Prüfstatus. |
| `weekly_presence.observed_without_expected_occurrence` | Sichtbare Kombinationen ohne erwarteten Montag-bis-Freitag-Termin, getrennt von Ausfall-/Wochenendfällen. |
| `weekly_presence.observed_cancellation_only` / `observed_weekend_only` | Sichtbare Kombinationen mit ausschließlich Ausfall- beziehungsweise Wochenendbezug. |
| `weekly_presence.blocked_details` / `review_details` | Blockierte beziehungsweise fachlich prüfpflichtige normalisierte Details. |
| `weekly_presence.partial_boundary_weeks` / `unobserved_expected_weeks` | Ausgeschlossene Randwochen beziehungsweise nicht beobachtete Wochen mit erwarteten Terminen. |
| `weekly_presence.weekend_occurrence_count` | Normalisierte Samstag-/Sonntagstermine innerhalb des Prüfzeitraums. Kein Vollständigkeitsnachweis. |
| `weekly_presence.comparable_pairs_match` | Übereinstimmung der vergleichbaren Kombinationen; bei nicht ausgewertetem Vergleich null. Keine Gesamtfreigabe. |

Die Detailnummern beziehen sich auf denselben vereinigten Zielbestand wie
`comparison`, nicht auf einen früheren Bericht. Blockierte Details können trotz
Übereinstimmung der vergleichbaren Kombinationen weiterhin fehlen. Ohne
`--details` bleiben die neuen Detail-/Präsenzberichte null. Bei einem
Detailabruf-/Parserfehler werden auch der vorherige Zielvergleich und die
Detailzähler verworfen; `status` ist `failed`, der Präsenzbericht null.

### Live-Ergebnis V0.0.27

Am 2026-10-21 wurden 26 Wochen und alle 66 bekannten Details der MT-Auswahl mit
konfigurierter Quellkennung geprüft: **100 HTTP-Anfragen**, keine Wiederholungen,
weiterhin eine Sekunde Mindestabstand. 65 Details lassen sich normalisieren,
eines bleibt durch die ungeklärte Einführungsbemerkung blockiert; 23 Vorschauen
bleiben fachlich prüfpflichtig. Die Zielmengen stimmen weiterhin überein.

Die Detailnormalisierung erwartet 809 Veranstaltungs-Wochen. 704 Kombinationen
sind in den Wochenansichten sichtbar und passen zu den Erwartungen.
**105 erwartete Wochenpräsenzen sind dort nicht sichtbar.** Keine sichtbare
Kombination ohne erwarteten Termin. Keine normalisierten Wochenendtermine;
daraus folgt keine vollständige Wochenendabdeckung. Es gibt im gewählten Zeitraum
keine unvollständigen Randwochen oder nicht beobachteten Erwartungswochen.

Die ausgegebenen Beispiele für Abweichungen betreffen Wochen mit Tageshinweisen.
Die Ursache aller 105 Abweichungen ist damit nicht belegt. Insbesondere dürfen
Ferienregeln nicht aus einer bloßen Wochenüberschrift abgeleitet oder fehlende
Einträge automatisch als Ausfall behandelt werden. Die zusätzliche Aufschlüsselung
je Woche und die strengere Abweisung doppelter Detailauswahl wurden nach dem
Live-Lauf lokal getestet. Keine Vorschau-Datei geändert, keine Rohdaten gespeichert,
kein Deployment oder eigener LXC-Lauf, keine Archivfreigabe.


## V0.0.28 – Abweichungen taggenau mit Tageshinweisen einordnen

Der bisherige Aufruf mit `--details` bleibt bestehen; zusätzliche Optionen oder
Konfiguration sind nicht nötig. Den neuen Stand vor dem LXC-Lauf veröffentlichen
und installieren. Der Abdeckungsbericht hat jetzt **Schema 3**. Der
Vorschauimport und dessen Schema 7 bleiben unverändert.

### Belegte Tagesbezeichnungen

Die Quelle wurde gezielt an den auffälligen Wochen geprüft. Vollständig belegte
Hinweise werden ohne ihren Freitext in feste Codes übersetzt:

| Vollständige Tagesbezeichnung | Code | Bedeutung der Einordnung |
| --- | --- | --- |
| `Weihnachtsferien` | `christmas_break` | Die Quelle zeigt genau diese Ferienbezeichnung an diesem Datum. |
| `Heilige Drei Könige` | `epiphany` | Die Quelle zeigt genau diese Tagesbezeichnung an diesem Datum. |
| Andere Bezeichnung oder Zusatz | `unclassified` | Inhalt nicht als belegte Bezeichnung eingeordnet. |

Dies sind **Hinweiscodes, keine Ausfallregeln**. Negierte oder erweiterte Texte
wie „Keine Weihnachtsferien“ oder „Weihnachtsferien außer Labor“ werden nicht
anhand einzelner Wörter erkannt. Unbekannte Hinweise erscheinen nur als Code,
nicht mit Freitext im Bericht. Die Tagesdaten und ihre Zuordnung zur angeforderten
Woche müssen weiterhin die Strukturprüfung bestehen.

`checked_weeks[].day_notices` enthält eine Liste aus `local_date` und `kind` für
die tatsächlich mit Hinweis versehenen Tage. Eine fehlgeschlagene Wochenprüfung
liefert keine bestätigten Tageshinweise. Der Wochenstatus bleibt auch bei
bekannten Codes `notes_require_review`.

### Taggenauer Kontext einer Abweichung

Bei jeder fehlenden Wochenpräsenz enthält der Bericht jetzt:

- `expected_local_dates`: unterschiedliche lokale Montag-bis-Freitag-Tage mit noch erwarteten Terminen. Explizit ausgefallene Termine sind bereits entfernt.
- `expected_day_notices`: nur Hinweise, deren Datum auf einen dieser erwarteten Tage fällt.
- `notice_assessment`: Einordnung des vorhandenen Kontexts, keine Freigabe.

| `notice_assessment` | Aussage |
| --- | --- |
| `all_expected_dates_with_known_notice` | Alle erwarteten Tage dieser fehlenden Wochenpräsenz haben einen der belegten Hinweiscodes. |
| `some_expected_dates_with_known_notice` | Nur ein Teil dieser erwarteten Tage hat einen belegten Code. |
| `unclassified_notice_on_expected_date` | Mindestens ein erwarteter Tag hat einen unbekannten Hinweis; keiner hat einen belegten Code. |
| `no_notice_on_expected_dates` | Auf keinem erwarteten Tag wurde ein Hinweis gefunden. Hinweise an anderen Tagen derselben Woche erklären die Abweichung nicht. |
| `day_notice_evidence_unavailable` | Für diese Woche wurde kein taggenauer Hinweisbestand übergeben. Nicht mit einem geprüften Bestand ohne Hinweise gleichsetzen. |

`weekly_presence.missing_notice_context_counts` zählt diese Kategorien über die
fehlenden Wochenpräsenzen. Dieselben Kategorien stehen pro Woche unter
`weekly_presence.weeks[].missing_notice_context_counts`. Jede fehlende
Veranstaltungs-Woche wird genau einmal gezählt, auch wenn mehrere Termine am selben
Tag liegen. Die Summe entspricht der Zahl der fehlenden Wochenpräsenzen.

Das Feld `day_notice_policy` lautet immer `context_only_no_automatic_exclusion`.
Die bisherigen Erwartungen und Abweichungen bleiben erhalten. Auch vollständig
mit bekannten Tageshinweisen versehene Erwartungen werden weder als Ausfall
übernommen noch automatisch aus der Vorschau entfernt. Ein Feiertags-/Ferienhinweis
kann allgemeine Lehre betreffen, ohne jeden Sondertermin auszuschließen.
`weekly_presence_mismatch`, fachliche Prüfhinweise, Exitcode 1 und die gesperrte
Archivfreigabe bleiben bestehen.

### Live-Ergebnis V0.0.28

Der vollständige Abgleich am 2026-10-21 erreicht erneut mit 100 seriellen
HTTP-Anfragen 26 Wochen und 66 semestergeprüfte Details der bekannten MT-Auswahl.
65 Details lassen sich normalisieren, eines bleibt blockiert, 23 Vorschauen
fachlich prüfpflichtig. 809 erwartete Veranstaltungs-Wochen und 704 passende
sichtbare Präsenzen ergeben weiterhin **105 Abweichungen**, keine unerwartete
sichtbare Präsenz.

| Woche | Erwartete Präsenzen | Passend sichtbar | Fehlend | Alle erwarteten Tage mit bekannten Codes | Unbekannter Hinweis auf erwartetem Tag |
| --- | ---: | ---: | ---: | ---: | ---: |
| KW 52/2026 | 46 | 23 | 23 | 23 | 0 |
| KW 53/2026 | 47 | 0 | 47 | 47 | 0 |
| KW 1/2027 | 48 | 13 | 35 | 12 | 23 |
| Summe auffälliger Wochen | 141 | 36 | 105 | 82 | 23 |

Alle übrigen verglichenen Wochen haben keine fehlende Wochenpräsenz. Belegte
Hinweise: Weihnachtsferien am 23.–25. und 28.–31. Dezember sowie 1. Januar;
„Heilige Drei Könige“ am 6. Januar. Die Hinweise am 4. und 5. Januar bleiben
`unclassified`. Gezielt geprüfte Vermutungen zu deren Bezeichnung wurden nicht
bestätigt und nicht in die Erkennung aufgenommen.

Die Verteilung grenzt die fachliche Prüfung auf drei Wochen ein. Sie bestätigt
keine pauschale Ferien-/Ausfallregel und löst den blockierten Einführungsfall
nicht. Nächster fachlicher Schritt: die unbekannten Tageshinweise und die
Verbindlichkeit der allgemeinen Unterbrechungen einschließlich möglicher
Sondertermine lokal an der Quelle klären. Die vorhandene Webseite bleibt
unverändert. Keine Rohdaten gespeichert, kein Deployment oder eigener LXC-Lauf,
keine Archivfreigabe.


## V0.0.29 – Unbenannte Quelltage von unbekannten Hinweisen trennen

Die bisher nicht eingeordneten Überschriften am 4. und 5. Januar 2027 enthalten
in der Planquelle exakt **`unbenannt`**. Es fehlt somit eine fachliche Bezeichnung;
die Erkennung soll daraus keine Ferienbezeichnung erfinden.

Der Abdeckungsbericht verwendet jetzt **Schema 4**. Der bisherige Aufruf mit
`--details` bleibt gültig, zusätzliche Konfiguration ist nicht nötig. Der
Semesterprüfbericht für den Vorschauimport bleibt bei Schema 7.

| Feld / Code | Bedeutung |
| --- | --- |
| `day_notices[].kind: unnamed` | Die Quelle zeigt exakt `unbenannt`. Die Bezeichnung fehlt. |
| `day_notices[].kind: unclassified` | Ein anderer, bislang nicht eingeordneter Hinweis liegt vor. |
| `unresolved_day_notices` | Datum und Code aller beobachteten unbenannten oder unbekannten Tageshinweise; auch ohne Detailabruf verfügbar. |
| `unnamed_day_notices_require_review` | Mindestens eine beobachtete Quellenbezeichnung fehlt. |
| `unclassified_day_notices_require_review` | Mindestens ein beobachteter Hinweis ist anderweitig ungeklärt. |
| `unnamed_notice_on_expected_date` | Bei einer fehlenden Wochenpräsenz trägt mindestens ein erwarteter Tag `unnamed`, keiner einen fachlich bekannten Code. |

`unnamed` gehört ausdrücklich **nicht** zu den fachlich bekannten Tagescodes.
Die Kategorie wird sowohl in den Gesamtsummen unter
`weekly_presence.missing_notice_context_counts` als auch je Woche ausgewiesen.
Wenn weitere erwartete Tage derselben Veranstaltung einen bekannten Code haben,
bleibt die Einordnung nur `some_expected_dates_with_known_notice`; die einzelnen
Tagescodes bleiben sichtbar. Andere unbekannte Hinweise werden nicht stillschweigend
zu `unnamed` umbenannt. Negierte oder erweiterte Texte und andere Schreibweisen
bleiben `unclassified`.

Auch nach dieser Einordnung bleiben `weekly_presence_mismatch`, die offenen
Tageshinweise, Exitcode 1 und `complete: false` bestehen. Der Bericht kennzeichnet
fehlende Quellenqualität; eine erkannte fehlende Bezeichnung ist keine erkannte
Ausfallregel. Die Textausgabe nennt diesen Umstand ausdrücklich.

### Unabhängige Kalenderreferenz

Die am 2026-10-21 von der offiziellen
[Semesterterminseite](https://www.hs-pforzheim.de/hochschule/die_hochschule/semestertermine)
verlinkte [Terminliste für Wintersemester 2026/27, Stand 19.05.2026](https://www.hs-pforzheim.de/fileadmin/user_upload/uploads_redakteur/Die_Hochschule/Die_Hochschule/aktuelle_Semestertermine/1NEU_Wintersemester2026_27.pdf)
nennt 23.12.2026 bis 06.01.2027 als vorlesungsfreien Weihnachtszeitraum. Beide
unbenannten Tage liegen darin. Das ist eine unabhängige fachliche Einordnung;
die fehlende Beschriftung der Planquelle wird dadurch nicht korrigiert.
Die aktuell verlinkte Fassung wurde einschließlich PDF-Inhalt geprüft,
statt ungeprüft einen älteren Suchtreffer zu verwenden.

Diese Referenz ist dokumentierte Recherche, keine fest eingebaute oder automatisch
geladene Kalenderkonfiguration. Sie ersetzt keine Prüfung veranstaltungsspezifischer
Ausnahmen. Die Anwendung überschreibt weder Quellhinweise noch Termine anhand der
Terminliste. Ohne eine explizite und getestete Ausnahmeregel darf aus einer
allgemeinen Unterbrechung insbesondere kein pauschaler Ausfall von Sonderterminen
abgeleitet werden.

### Prüfnachweis

Live am 2026-10-21: 100 serielle HTTP-Anfragen, 26 Wochen und 66 semestergeprüfte
Details. 65 Details normalisierbar, eines blockiert; 23 Vorschauen fachlich
prüfpflichtig. Die 105 fehlenden Wochenpräsenzen bleiben bestehen: 82 mit
spezifisch bekannten Tageshinweisen, 23 nun mit `unnamed_notice_on_expected_date`.
Keine anderen unbekannten Tageshinweise, keine zusätzliche sichtbare Präsenz.
`unresolved_day_notices` enthält genau 2027-01-04 und 2027-01-05 mit `unnamed`.
443 lokale Tests erfolgreich, auch unter geerbter fiktiver Betreiberkonfiguration.
Footer und die drei Bash-Anleitungsblöcke geprüft.
Die vorhandene Web-Vorschau wird durch den Abgleich nicht aktualisiert. Der
Einführungsfall, mögliche Sondertermine, Wochenenden und die vollständige
Archivfreigabe bleiben weiterhin offen.

## Ab V0.0.30: vollständiger Import statt Präsenzdiagnose

Der hier beschriebene Befehl bleibt eine Diagnose ohne Speicherung und ohne Freigabe. Für explizite Ferienregeln, Einzelterminabgleich einschließlich Zeiten und Raum, eine gebundene Fachprüfung und sichere SQLite-Archivierung den neuen [Kalenderimport](calendar-import.md) verwenden. Seine Freigabe ist von der bisherigen konservativen Abdeckungsdiagnose getrennt.
