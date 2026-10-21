# Wochen- und Semesteransichten abgleichen – V0.0.26

`source-coverage-check` vergleicht die Veranstaltungsziele beider Semesteransichten
mit den Zielen ausdrücklich gewählter Wochen. Der Befehl liest keine Detailseiten
und schreibt weder Archivdaten noch eine Vorschau-Datei. Eine vorhandene
Web-Vorschau bleibt unverändert.

## Im LXC ausführen

Zuerst V0.0.26 auf GitHub veröffentlichen und das bestehende
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

## Bereinigter Bericht (eigener Vertrag, Schema 1)

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
der Befehl endet mit **Exitcode 1**. Der Abgleich prüft weder sämtliche
Einzeltermine, deren Uhrzeiten und Räume noch Semesterangaben auf Detailseiten.
Er veröffentlicht und aktualisiert keine Daten auf der Webseite.

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
