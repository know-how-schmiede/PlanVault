# Wochennavigation und Abgleich – V0.0.8

Der Importbaustein liest die datierten Einträge der beobachteten Wochenauswahl.
Wochennummer, Montag und Sonntag müssen zueinander passen. Das ISO-Jahr wird
aus dem Montag ermittelt, damit der Jahreswechsel korrekt bleibt. Doppelte,
ungültige oder mehrdeutige Auswahlen führen zum Abbruch. Undatierte
Semester-/Sonderansichten werden nicht als Wochen ausgegeben.

Die ausgewählte Woche wird mit dem bestehenden Formularparser über die
beobachtete Schaltfläche „anzeigen“ angefordert. Feldnamen und Optionswerte
werden aus der jeweiligen Antwort gelesen und bleiben im Arbeitsspeicher.
Es gibt keine fest eingebauten Quellparameter.

## Was geprüft wird

- Die angeforderte Woche muss angeboten werden und im angegebenen Prüfzeitraum liegen.
- Die Antwort muss diese Woche ausdrücklich als ausgewählt markieren.
- Die sichtbaren Tagesüberschriften müssen exakt Montag bis Freitag dieser Woche zeigen.
- Das angebotene Wochenverzeichnis darf sich während des Ablaufs nicht ändern.
- Loginseiten, Fehler, unbekannte Strukturen und Abruflimits führen nicht zu gültigen leeren Plänen.

| Ergebnis | Bedeutung |
| --- | --- |
| `ok` | Wochenstruktur und Tagesdaten passen; bekannte Veranstaltungsblöcke vorhanden |
| `notes_require_review` | Zusätzliche Hinweise in Tagesüberschriften, etwa Ferien, müssen fachlich geprüft werden |
| `empty_unverified` | Keine bekannten Veranstaltungsblöcke; keine bestätigte leere Planung |
| `failed` | Abruf oder Strukturprüfung fehlgeschlagen |

Beim ersten ungeklärten oder fehlgeschlagenen Ergebnis endet der Abruf.
Nachfolgende, nicht geprüfte Wochen bleiben fehlend. Auch im Auswahlmenü
angebotene Wochen zählen erst nach einem geprüften Abruf.

`check_week_coverage` vergleicht die Ergebnisse mit einem **unabhängig
angegebenen Zeitraum**. Er übernimmt nicht einfach den ersten und letzten
Eintrag des Quellmenüs als Beweis für einen vollständigen Semesterumfang.

## Manueller Test

Nach Veröffentlichung und Installation von V0.0.8, mit gesetztem `LSF_BASE_URL`:

```bash
python -m flask --app backend source-weeks-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)" \
  --start 2026-08-31 --end 2027-02-28 \
  --week 2026-W44 --week 2026-W53
```

Suchtext und Titel sind fiktive Platzhalter; Zeitraum und Wochen ebenfalls
bewusst für die gewünschte Prüfung festlegen. Jede Woche wird ausdrücklich
angegeben; es startet kein automatischer Abruf sämtlicher Semesterwochen.
Für die Ausführung unter dem Dienstkonto im Container den in
[Quelltest](source-check.md) beschriebenen `systemd-run`-Aufbau verwenden und
den abschließenden Flask-Befehl entsprechend ersetzen.

Der Befehl zeigt nur ISO-Wochen, Prüfstatus und Anzahlen an. Bei fehlenden oder
ungeklärten Wochen endet er mit Fehlerstatus 1 – auch bei einer absichtlich
unvollständigen Stichprobe. Bei vollständig passenden Wochenantworten endet
er mit Status 0, bestätigt jedoch weiterhin keinen vollständigen Datenimport.

## Nachweis und Grenzen

Am 2026-10-20 wurden 26 angebotene Wochen erkannt. Die neue Implementierung
prüfte exemplarisch KW 44/2026 und KW 53/2026 live. KW 44 erhielt `ok`, KW 53
wegen Ferienhinweisen `notes_require_review`. Der Abgleich meldete 24 fehlende
Wochen und eine prüfpflichtige Woche. Der Ablauf einschließlich Studiengangssuche
benötigte acht HTTP-Anfragen. Rohseiten und Quelladressen wurden nicht gespeichert.

146 lokale Tests bestehen. Ein vollständiger Semesterabruf wurde nicht
durchgeführt. Wochenendtermine, Sonderansichten, Filter, Detailseiten und
Gruppenzuordnungen benötigen weitere Nachweise. Die Zahl bekannter Blöcke sagt
nichts über eindeutige Veranstaltungen oder vollständig gelesene Termine aus.
`WeekAudit.complete` bleibt immer `False`; es wird kein Archivstand veröffentlicht.
Die Website zeigt weiterhin die Startseite mit Versionsfooter.


## Ergänzung V0.0.26 – Fortsetzung bei Prüfhinweisen im Ansichtsabgleich

Der neue [Ansichtsabgleich](view-comparison.md) nutzt dieselbe strukturelle
Wochenprüfung. Nur dort wird die Prüfung nach Tageshinweisen oder ungeklärt
leeren Wochen fortgesetzt. Die Statuswerte bleiben unverändert prüfpflichtig.
Auch Seiten mit Tageshinweisen können beobachtete Veranstaltungsziele beitragen.
Struktur- und Abruffehler stoppen weiterhin sofort. Bestehende Wochen- und
Importprüfbefehle behalten ihr bisheriges Abbruchverhalten.
