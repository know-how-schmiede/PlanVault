# Timeline

Alle Änderungen einer Version werden in einem gemeinsamen Eintrag zusammengefasst. Neue Versionen stehen oben.

## V0.0.22 – Wochenansicht für die Import-Vorschau

**Datum:** 2026-10-20

**Änderungen:**

- Zentrale Version auf Userwunsch auf `0.0.22` gesetzt.
- Vorschau standardmäßig als responsive Wochenansicht von Montag bis Sonntag dargestellt; Datum, Uhrzeit, Raum, Lehrperson und Prüfhinweise bleiben sichtbar.
- Navigation zwischen erfassten Wochen und Wechsel zur Listenansicht ergänzt. Auswahl aktueller, nächster oder letzter erfasster Woche anhand der lokalen ISO-Kalenderwoche.
- Tage und Wochen ohne erfasste Termine werden nicht als bestätigte Freizeiten dargestellt. Zeitgleiche Termine bleiben erhalten; keine Archivfreigabe.
- Vorschau-Dateiformat unverändert, kein erneuter Import für die Darstellung nötig. Anleitung, Startseite, README und Roadmap aktualisiert.
- Bebilderte Webseitenbeschreibung mit den bereitgestellten Screenshots von Startseite und Listen-Vorschau ergänzt und in der README verlinkt. Erfolgreiche Ergebnisanzeige und Kalenderwochenfilter im Serverbetrieb durch den Nutzer bestätigt; die Screenshots zeigen noch nicht die neue Wochenansicht.

**Prüfung:** 298 lokale Tests erfolgreich, einschließlich Jahreswechsel, lokaler Tageszuordnung, Zeitumstellung, überlappender Termine, Navigation, Ansichtswechsel und weiterhin sicherer HTML-Ausgabe. HTML/CSS geprüft; bereitgestellte Screenshots für die Webseitenbeschreibung visuell geprüft. Kein eigener Browser-Livetest, Deployment oder neuer Live-Import. Der Nutzer bestätigt die Ergebnisanzeige mit Kalenderwochenfilter auf dem Server. `git diff --check` ohne Fehler.

**Commit-Kurzbeschreibung:** Version 0.0.22 mit Wochenansicht, Navigation und bebilderter Webseitenbeschreibung ergänzen

## V0.0.21 – Unvollständige Import-Vorschau auf der Webseite

**Datum:** 2026-10-20

**Änderungen:**

- Zentrale Version auf Userwunsch auf `0.0.21` gesetzt.
- Startseitenlink und responsive Terminliste mit Kalenderwochenfilter, Raum, Lehrperson und lokalem Erstellungszeitpunkt ergänzt.
- Dauerhafte Kennzeichnung als unvollständige Vorschau ohne Archivfreigabe; blockierte Details werden gezählt, fachlich prüfpflichtige Termine markiert.
- Manueller Semesterprüflauf kann mit `--save-preview` und lokal konfiguriertem `PREVIEW_FILE` eine separate Vorschau schreiben. Kein Quellabruf durch Webseitenbesuche.
- Atomarer Dateiaustausch, Größen- und Inhaltsprüfung sowie Schutz der bisherigen Vorschau bei Fehlern oder leeren Ergebnissen. Keine Quelladressen, Cookies oder Freitextbemerkungen gespeichert; HTML wird bei Anzeige escaped.
- Einrichtung und Import für den bestehenden Debian-LXC dokumentiert, README und Roadmap aktualisiert.

**Prüfung:** 291 lokale Tests erfolgreich, einschließlich Speichern/Lesen, CLI-Anbindung, Fehlererhalt, ungültigen Dateien, Kalenderwochenfilter, lokaler Zeit und HTML-Escaping. Kein echter Vorschauimport und kein Deployment im Ziel-LXC. Keine Browser-Sichtprüfung; HTML und CSS lokal geprüft. Keine Archivveröffentlichung.

**Commit-Kurzbeschreibung:** Version 0.0.21 mit gekennzeichneter Import-Vorschau und Kalenderwochenfilter ergänzen

## V0.0.20 – Anfängeranleitung und Wochentagsabgleich

**Datum:** 2026-10-20

**Änderungen:**

- Zentrale Version auf Userwunsch auf `0.0.20` gesetzt; Footer bezieht sie weiterhin daraus.
- Erstinstallation und Update mit Container-Konsole, aktuellem wget-Aufruf, Eingaben, Erfolgskontrolle und häufigen Fehlern erklärt. Kurzfassung unter scripts synchronisiert.
- Nächsten Baustein zur Import-Vollständigkeit umgesetzt: Schema 5 vergleicht sichtbare Tagesüberschriften und lokale Termintage, zählt blockierte Details separat und behauptet keine Wochenend-Vollständigkeit.
- Erfolgreichen Betrieb nach V0.0.19 durch den User festgehalten. Offene Bemerkungen bleiben blockiert; kein Archiv veröffentlicht.

**Prüfung:** 279 lokale Python-Tests und 14 isolierte Skript-Eingabetests erfolgreich. Sieben dokumentierte Bash-Blöcke sowie beide Skripte auf Syntax geprüft; git diff --check ohne Fehler. Begrenzte Quellenprüfung ohne ausreichenden neuen Beleg zur Freigabe der offenen Bemerkungen. Kein Deployment und kein vollständiger Live-Semesterlauf für diese Version.

**Commit-Kurzbeschreibung:** Version 0.0.20 mit Anfängeranleitung und Wochentagsabgleich ergänzen

## V0.0.19 – Kompaktes Logo und nächste Schritte auf der Startseite

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.19` gesetzt; Footer übernimmt die Version.
- Webseitenlogo durch die unveränderte Datei „WI-PlanArchiv_ Vorlesungsplanung gesichert.png“ ersetzt.
- Logo und Einführungstext nebeneinander in einer responsiven 1:3-Spaltenaufteilung angeordnet. Die Logospalte bleibt inklusive schmaler Ansichten unter 25 Prozent der Inhaltsbreite; keine Verzerrung des Bildes.
- Überschrift „Dein Vorlesungsplan …“ und Beschreibung rechts neben dem Logo platziert, zusätzlichen Slogan entfernt.
- Nächste Schritte sichtbar ergänzt: vollständigen Import absichern, Archivstände sicher speichern, Wochen-/Listenansicht entwickeln. Noch keine umgesetzten Archivfunktionen behauptet.
- Erfolgreiches Server-Update nach V0.0.18 durch den User bestätigt; Installationsanleitung und Roadmap entsprechend aktualisiert.

**Prüfung:** 274 lokale Tests erfolgreich, einschließlich korrekter Logodatei, Startseiteninhalt und zentraler Version. `git diff --check` ohne Fehler. Layout über HTML und CSS geprüft; keine Browser-Sichtprüfung durchgeführt. V0.0.19 noch nicht auf dem Server installiert. Der User bestätigt das vorherige Update, nicht eine Erstinstallation oder Vollständigkeit des Datenimports.

**Commit-Kurzbeschreibung:** Version 0.0.19 mit kompaktem Logo, seitlichem Einführungstext und nächsten Schritten ergänzen

## V0.0.18 – Logo, Installation ohne curl und geprüfte Klausurzeiten

**Datum:** 2026-10-20

**Änderungen:**

- Version zentral auf Userwunsch auf `0.0.18` gesetzt.
- Vorhandenes Logo als lokale statische Bilddatei in den gemeinsamen Seitenkopf eingebunden; responsive Breite, unverzerrtes Seitenverhältnis und zugänglicher Startseitenlink.
- Verpflichtende curl-Abhängigkeit aus Installer und Update entfernt. HTTP-Prüfung über Python-Standardbibliothek mit festem Loopback-Ziel, ohne Proxy, mit Timeout und Größenlimit. Update prüft die exakte Version; Sicherung und Rollback bleiben erhalten.
- Download-Anleitungen auf wget mit temporärem Ziel und Fehlerkette umgestellt; Arbeitsanweisungen ergänzt.
- Zwei offene Normalisierungsfälle untersucht. Eindeutige Klausurzeiten innerhalb eines reservierten Einzeltermins unterstützt, mit erhaltenen Tabellenzeiten und Prüfhinweis. Eine Veranstaltung mit Begrüßungs-/Einführungsbemerkungen bleibt gesperrt.
- Fiktive Tests, README, Roadmap und Fachanleitungen aktualisiert.

**Prüfung:** 274 lokale Tests erfolgreich, einschließlich HTTP-Fehlern, falscher Version, Größenlimit, Timeout, Logo-Auslieferung und Klausurzeit-Grenzfällen. Bash-Syntax beider Skripte und 14 isolierte Eingabetests erfolgreich. Quellenanalyse mit 74 HTTP-Anfragen und anschließenden begrenzten Detailprüfungen; abschließender gezielter Live-Test mit zehn Anfragen: ein neu normalisiertes Detail und eines weiter blockiert. Kein erneuter vollständiger Import nach der Änderung. Browser-Sichtprüfung mangels verfügbarer Browseroberfläche nicht möglich; HTML, CSS und Bildauslieferung lokal geprüft. Keine Installation oder Update-Ausführung im Ziel-LXC, keine Archivveröffentlichung.

**Commit-Kurzbeschreibung:** Version 0.0.18 mit Webseitenlogo, curl-freien Skripten und geprüften Klausurzeiten ergänzen

## V0.0.17 – Bisher übersehene Veranstaltungsblöcke erfassen

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.17` gesetzt; Footer übernimmt die Version.
- Zweite Veranstaltungsblock-Darstellung live geprüft und in Detail-, Wochen-, Semester- und Strukturprüfung gemeinsam unterstützt. Acht Zeilen und genau ein Detailverweis bleiben Pflicht.
- Die vermeintlich leere Zusatzansicht enthält 98 Blöcke und 33 eindeutige Ziele. Die Semesteransicht enthält insgesamt 162 Blöcke und 66 Ziele: zwölf mehr als mit dem bisherigen Sammler.
- Gemischte Darstellungen dedupliziert; Raumlinks und unvollständige Blockstrukturen weiterhin abgelehnt.
- Semesterbericht auf Schema 4 mit Blockanzahl und beobachteten Wochentagen erweitert. Sichtbare Tagesüberschriften bestätigen keine Inhaltsvollständigkeit.
- Anleitung auf das explizite Detailbudget 80 für die 66 Ziele angepasst; Standard 60 und harte HTTP-Grenze 100 bleiben erhalten.
- Fiktive Tests, README, Roadmap und Quellenanalyse aktualisiert; frühere Leerinterpretation ausdrücklich korrigiert.

**Prüfung:** 257 lokale Tests erfolgreich. Begrenzte Strukturproben sowie abschließender Live-Lauf mit 74 HTTP-Anfragen: alle 66 Details geparst, 64 Vorschauen erzeugt (davon 21 mit fachlichen Prüfhinweisen), zwei Details weiterhin blockiert. Beide Ansichten zeigen Montag bis Freitag; keine Wochenendtermine in den erzeugten Vorschauen. Daraus folgt kein Vollständigkeitsnachweis für Wochenenden. Keine Rohseiten oder vertraulichen Werte gespeichert. `git diff --check` ohne Fehler. Kein Deployment im LXC; Speicherung und Webanzeige bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.17 mit zusätzlicher Blockdarstellung und korrigierter Semestererfassung ergänzen

## V0.0.16 – Verlegungs- und Serienhinweise erhalten

**Datum:** 2026-10-20

**Änderungen:**

- Version zentral auf Userwunsch auf `0.0.16` gesetzt; Footer übernimmt die Version.
- Explizite Ausfälle auch mit zusätzlichen Datumsangaben im Hinweis verarbeitet. Hinweistexte bleiben erhalten und gesondert prüfpflichtig; keine Ersatztermine erzeugt oder mit Einzelterminen verknüpft.
- Ungültige führende Ausfalldaten und mehrdeutige Angaben bleiben gesperrt. Allgemeine Serienbemerkungen werden nicht automatisch als Terminregeln interpretiert.
- Bei blockierter Normalisierung vollständig geparste Veranstaltungsdaten intern als `unresolved_course` erhalten. Keine Teilvorschau, keine Ausgabe der Inhalte im CLI-Bericht, keine Speicherung auf Datenträger.
- Belegte Serienbemerkungen „Vorlesung“, „Nachholtermin“ bei explizitem Einzeltermin sowie Laborraumhinweise als Annotation mit Serienbezug erhalten. Keine Änderung von Datum, Uhrzeit oder Raumfeld; unbekannte Bemerkungen bleiben gesperrt.
- Fiktive Tests, README, Roadmap und Quellenanalyse aktualisiert; Semesterbericht bleibt bei Schema 3.

**Prüfung:** 248 lokale Tests erfolgreich. Der erste Live-Lauf dieser Version prüfte 54 Details mit 62 HTTP-Anfragen: 51 Vorschauen und drei blockierte Veranstaltungen mit vier Serienbemerkungen. Diese Bemerkungen wurden anschließend in einem erneuten Diagnose-Lauf und begrenzten Detailabrufen klassifiziert. Abschließende gezielte Prüfung der drei betroffenen Veranstaltungen: drei Vorschauen, alle vier Hinweise erhalten, elf HTTP-Anfragen. Alle drei Vorschauen bleiben fachlich prüfpflichtig; insbesondere weicht der Laborraumhinweis vom Raumfeld ab. Kein erneuter vollständiger Lauf nach der letzten Änderung. Keine Rohseiten oder vertraulichen Werte gespeichert. `git diff --check` ohne Fehler. Vollständigkeitsnachweis, Speicherung und Webanzeige bleiben offen; kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.16 mit erhaltenen Verlegungs- und geprüften Serienhinweisen ergänzen

## V0.0.15 – Mehrfache Ausfälle und klare Normalisierungsdiagnose

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.15` gesetzt; Footer übernimmt sie.
- Die 21 Prüffälle aus V0.0.14 in 19 blockierte Normalisierungen und zwei Vorschauen mit Prüfhinweisen aufgeschlüsselt.
- Mehrere aufeinanderfolgende Ausfallangaben und fehlende Ausfallhinweise unterstützt. Hinweise bleiben dem jeweiligen Ausfall zugeordnet; doppelte oder ungültige Angaben verhindern eine Teilvorschau.
- Numerische Raumkennungen mit drei Zahlenteilen nicht mehr pauschal als zusätzliche Kurzdatumsangabe gewertet. Mögliche Ersatztermine bleiben ungeklärt; keine automatische Ableitung aus Freitext.
- Semesterbericht auf Schema 3 mit getrennten Zählern für Vorschauen, blockierte Details und Vorschauen mit Prüfhinweisen erweitert.
- Fiktive Tests, README, Roadmap und Fachanleitungen aktualisiert.

**Prüfung:** 235 lokale Tests erfolgreich. Ein Diagnose- und ein abschließender Live-Lauf mit jeweils 62 HTTP-Anfragen. Nach der Änderung: 54 Detailziele geprüft, 50 Vorschauen erzeugt, davon 17 mit fachlichen Prüfhinweisen; vier Details weiterhin technisch blockiert (vorher 19). Keine Rohseiten oder vertraulichen Quellwerte gespeichert. `git diff --check` ohne Fehler. Vollständigkeitsnachweis, Archivspeicherung und Webanzeige bleiben offen; kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.15 mit mehrfachen Ausfällen und getrennter Normalisierungsdiagnose ergänzen

## V0.0.14 – Alle bekannten Semesterdetails prüfen

**Datum:** 2026-10-20

**Änderungen:**

- Version zentral auf Userwunsch auf `0.0.14` gesetzt; Footer übernimmt die Version.
- Semesterprüfbefehl um `--details`, erwartetes Semester, lokale Studiengangs-/Prüfungsordnungskennungen und Detailbudget erweitert.
- Alle eindeutigen Ziele beider Semesteransichten werden sequenziell geprüft. Budgetüberschreitung bricht vor dem ersten Detailabruf ab, statt still eine Stichprobe zu erzeugen.
- Jede Detailseite muss zum erwarteten Semester passen. Abruf- oder Parserfehler liefern keine erfolgreiche Teilprüfung; ungeklärte Normalisierungen bleiben sichtbar.
- Bereinigten Semesterbericht auf Schema 2 mit Detailzählern und `known_details_checked` erweitert. Keine Archivfreigabe oder Speicherung.
- Tests, Anleitung, README, Roadmap und Quellenanalyse aktualisiert.

**Prüfung:** 226 lokale Tests erfolgreich. Einmaliger Live-Lauf mit 62 HTTP-Anfragen einschließlich Navigation: alle 54 bekannten Detailziele geparst und gegen das erwartete Semester geprüft; 21 Details haben offene Normalisierungsfragen oder Prüfhinweise. Keine Quellseiten oder vertraulichen Werte gespeichert. `git diff --check` ohne Fehler. Vollständigkeit der Quelle, leere Zusatzansicht, Wochenenden und fachliche Zuordnungen bleiben offen; kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.14 mit budgetierter Prüfung aller bekannten Semesterdetails ergänzen

## V0.0.13 – Zusätzliche Semesteransichten prüfen

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.13` gesetzt; gemeinsamer Footer übernimmt die Version.
- Semesteransicht und Block-/Einzelterminansicht über sichtbare Auswahlbeschriftungen erschlossen.
- `source-semester-check` mit optionalem bereinigtem JSON-Bericht ergänzt. Konfigurierte Quellkennung ist Voraussetzung; maximal zwölf HTTP-Anfragen, keine Detailabrufe.
- Übernahme der Ansicht, unverändertes Wochenangebot, Struktur und Kennungen geprüft. Zusätzliche Detailziele der zweiten Ansicht werden gezählt.
- Leere Ansichten bleiben ungeklärt; Fehler führen zu keiner erfolgreichen Teilbestandsaufnahme. Vollständigkeit und Veröffentlichung bleiben gesperrt.
- Fiktive Tests, Anleitung, README, Roadmap und Quellenanalyse ergänzt.

**Prüfung:** 216 lokale Tests erfolgreich. Implementierter Adapter live mit acht HTTP-Anfragen geprüft: 54 eindeutige Detailziele in der Semesteransicht, Block-/Einzelterminansicht ohne erkannte Blöcke und daher `empty_unverified`. Begrenzte Vorprüfungen dienten der Strukturanalyse. Keine Quelladressen, echten Parameter oder Rohseiten gespeichert. `git diff --check` ohne Fehler. Vollständiger Semesterimport, Speicherung und Webanzeige bleiben offen; kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.13 mit begrenzter Prüfung zusätzlicher Semesteransichten ergänzen

## V0.0.12 – Konfigurierbare Veranstaltungsidentität

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.12` gesetzt; Footer übernimmt sie automatisch.
- Numerische Quellkennung in getrennten HTTP-Sitzungen geprüft: 47 Detailziele behalten dieselbe Identität.
- Lokale Einstellungen `LSF_ID_PARAMETER` und `LSF_ID_NAMESPACE` ergänzt. Keine echten Parameter oder Quellwerte im Repository hinterlegt.
- Detailziele mit konfigurierter Kennung unabhängig von Sitzungswerten zusammengeführt. Mehrdeutige, fehlende oder widersprüchliche Zuordnungen brechen ab.
- Ohne Konfiguration bleibt die bisherige laufbezogene Zuordnung aktiv. Studiengangs-/Prüfungsordnungszuordnung bleibt ausdrücklich prüfpflichtig.
- Importbericht auf Schema 2 mit Identitätsmodus erweitert; Dokumentation, Roadmap und Quellenanalyse aktualisiert.

**Prüfung:** 203 lokale Tests erfolgreich. Abschließender Live-Vergleich über zwei unabhängige Sitzungen mit insgesamt zwölf HTTP-Anfragen: alle 47 Paare aus Titel und Kennung stimmen überein, auch bei gleichnamigen Veranstaltungen. Weitere begrenzte Vorprüfungen dienten der Feldanalyse. Keine Rohseiten oder vertraulichen Quellwerte gespeichert. `git diff --check` ohne Fehler. Keine vollständige Semestererfassung, Archivveröffentlichung oder Installation im LXC; die lokale Kennungskonfiguration muss vor Nutzung gesetzt werden.

**Commit-Kurzbeschreibung:** Version 0.0.12 mit konfigurierbarer sitzungsunabhängiger Veranstaltungskennung ergänzen

## V0.0.11 – Live-belegte Einzeltermine und Ausfälle

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.11` gesetzt.
- Drei weitere Detailseiten gezielt untersucht; erstmals eine Kombination aus wöchentlicher Serie, Einzeltermin und Ausfallhinweis live belegt.
- Rhythmus `Einzel` für genau ein Datum standardmäßig unterstützt; mehrtägige Angaben weiterhin abgelehnt.
- Ausfallformat `Datum: Hinweis` ergänzt. Ausgefallene Termine werden separat mit Datum, Serienbezug und Hinweis erhalten; keine automatische Zuordnung eines Ersatztermins.
- Prüfhinweise in Detail-CLI und gemeinsamem Importbericht vereinheitlicht. Auch eine erzeugte Vorschau kann fachlich prüfpflichtig bleiben.
- Fiktive Sonderfall-Fixture, Tests, README, Roadmap und Quellenanalyse aktualisiert.

**Prüfung:** 189 lokale Tests erfolgreich. Abschließender Live-Test mit sieben HTTP-Anfragen: zwei Serien, 16 Vorschautermine, ein separat erhaltener Ausfall; fachliche Prüfhinweise bleiben bestehen. Keine Rohseiten, Quelladressen oder realen Hinweistexte gespeichert. `git diff --check` ohne Fehler. Vollständiger Semesterimport, stabile Identität, Speicherung und Webanzeige bleiben offen; kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.11 mit live belegten Einzelterminen und erhaltenen Ausfallhinweisen ergänzen

## V0.0.10 – Gemeinsamer Import-Prüflauf und JSON-Bericht

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.10` gesetzt.
- Navigation, Wochenabgleich und Detailstichprobe zu einem gemeinsamen Prüflauf verbunden.
- Gleiche Detailziele aus mehreren geprüften Wochen zusammengeführt; keine Detailabrufe nach ungeklärten Wochenantworten.
- Bereinigten Bericht mit Lauf-ID, UTC-Zeitstempeln, Versionsangabe, Phasen, Anzahlen und offenen Punkten ergänzt. Keine Quelladressen oder Veranstaltungsdaten im Bericht.
- Befehl `source-import-check` mit optionaler JSON-Ausgabe ergänzt. Vollständigkeit und Veröffentlichung bleiben ausdrücklich unbestätigt.
- README, Roadmap, Quellenanalyse und Anleitung aktualisiert.

**Prüfung:** 178 lokale Tests erfolgreich. Gemeinsamer Live-Prüflauf mit zehn HTTP-Anfragen: KW 43/2026 und KW 44/2026 passend, 51 unterschiedliche Detailziele, zwei Details geprüft; 24 fehlende Wochen und 49 ungeprüfte Ziele korrekt ausgewiesen. Keine Rohseiten oder Quelladressen gespeichert. `git diff --check` ohne Fehler. Kein vollständiger Semesterimport, keine Archivveröffentlichung und kein Deployment im LXC.

**Commit-Kurzbeschreibung:** Version 0.0.10 mit gemeinsamem Import-Prüflauf und bereinigtem JSON-Bericht ergänzen

## V0.0.9 – Detailzuordnung und begrenzte Importstichprobe

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.9` gesetzt.
- Veranstaltungslinks anhand der beobachteten Blockstruktur gesammelt und von Raumlinks getrennt.
- Identische absolute Ziele innerhalb des Prüflaufs zusammengefasst; unterschiedliche Ziele niemals allein anhand des Titels zusammengeführt.
- Begrenzten Detailabruf mit Semesterprüfung, Parser und Kalendervorschau verbunden. Fehler verhindern ein erfolgreiches Teilergebnis; ungeklärte Normalisierung bleibt markiert.
- Befehl `source-details-check` ergänzt: explizite Woche, erwartetes Semester, lokale Zuordnungskennungen und maximal zehn Detailziele.
- README, Roadmap, Quellenanalyse und Anleitung aktualisiert.

**Prüfung:** 166 lokale Tests erfolgreich. Live-Stichprobe mit acht HTTP-Anfragen: 53 Blöcke, 47 unterschiedliche Detailziele; zwei Details mit einer beziehungsweise zwei Serien verarbeitet, 45 Ziele ungeprüft. Keine Rohseiten oder Quelladressen gespeichert. `git diff --check` ohne Fehler. Dauerhafte Quellidentität, vollständiger Semesterimport und Deployment im LXC bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.9 mit Detailzuordnung und begrenzter Importstichprobe ergänzen

## V0.0.8 – Wochennavigation und Abdeckungsprüfung

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.8` gesetzt.
- Datierte Wochenauswahl mit Prüfung von Datumsbereich, ISO-Jahr, Wochennummer und Eindeutigkeit ergänzt.
- Wochenwechsel über beobachtete Formularwerte mit Prüfung der ausgewählten Woche und sichtbaren Tagesüberschriften verbunden.
- Wochenantworten gegen einen unabhängig angegebenen Zeitraum abgeglichen. Nicht besuchte Wochen bleiben fehlend; ungeklärte leere Ansichten und Ferienhinweise verhindern eine Vollständigkeitsmeldung.
- Manuellen Befehl `source-weeks-check` für ausdrücklich ausgewählte Wochen ergänzt. Beim ersten ungeklärten Ergebnis stoppt die Prüfung.
- README, Roadmap, Quellenanalyse und Bedienungsanleitung aktualisiert.

**Prüfung:** 146 lokale Tests erfolgreich. Live-Stichprobe mit acht HTTP-Anfragen: 26 angebotene Wochen, KW 44/2026 strukturell passend, KW 53/2026 wegen Ferienhinweisen prüfpflichtig; 24 fehlende Wochen korrekt gemeldet. Keine Quelladressen oder Rohseiten gespeichert. `git diff --check` ohne Fehler. Vollständiger Semesterimport, Wochenend-/Sonderterminerfassung und Deployment im Zielcontainer bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.8 mit Wochennavigation und strenger Abdeckungsprüfung ergänzen

## V0.0.7 – Live-geprüfte Studiengangsnavigation

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.7` gesetzt.
- Studiengangssuche über sichtbare Feldbeschriftungen, eindeutige Trefferlinks und ausdrücklich benannte Suchschaltflächen implementiert. Keine realen Quellparameter im Code hinterlegt.
- Normale Fieldsets und gleichwertige doppelte Submit-Schaltflächen unterstützt; schreibgeschützte Studiengangsanzeige mit versteckter Auswahl korrekt erhalten.
- Manuellen Befehl `source-plan-check` ergänzt; Ergebnisse bleiben reine Navigationsprüfung ohne Archivveröffentlichung.
- README, Roadmap, Quellenanalyse und Bedienungsanleitung aktualisiert.

**Prüfung:** 122 lokale Tests erfolgreich, einschließlich Versionsfooter und Navigation. Ablauf Einstieg → Suche → Treffer → Auswahlbestätigung → Planantwort für den bereits untersuchten Studiengang live erfolgreich: sechs HTTP-Anfragen einschließlich Weiterleitungen, 53 bekannte Veranstaltungsblöcke. Keine Rohseiten, Quelladressen oder Formularparameter gespeichert. Vorheriger Versuch mit fünf Anfragen wurde erwartungsgemäß vom Budget gestoppt. Kein vollständiger Semesterimport und kein Deployment im LXC; `git diff --check` ohne Fehler.

**Commit-Kurzbeschreibung:** Version 0.0.7 mit live geprüfter Studiengangsnavigation ergänzen

## V0.0.6 – Geprüfte Formularnavigation

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.6` gesetzt.
- Formularauswahl anhand expliziter Feldnamen sowie GET-/POST-Übermittlung über die bestehende HTTP-Sitzung ergänzt.
- Versteckte und wiederholte Felder, Textbereiche, Auswahlen und explizite Suchschaltflächen unterstützt; unerlaubte Überschreibungen und mehrdeutige Strukturen abgelehnt.
- Ausschließlich fiktive Formulartests ergänzt; keine realen Navigationsparameter hinterlegt.
- README, Roadmap und Quellenanalyse um Funktionsumfang und offene Live-Zuordnung ergänzt.

**Prüfung:** 106 lokale Tests erfolgreich, einschließlich Formularnavigation, HTTP-Adapter, Parser und Versionsfooter; `git diff --check` ohne Fehler. Keine Live-Navigation und keine Bereitstellung im LXC durchgeführt; automatischer Semesterimport bleibt offen.

**Commit-Kurzbeschreibung:** Version 0.0.6 mit validierter Formularnavigation ergänzen

## V0.0.5 – HTTP-Abrufadapter und manueller Quelltest

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.5` gesetzt; Website-Betrieb nach vorherigem Update vom User bestätigt.
- HTTPS-Abrufadapter mit temporären Cookies, gleichem Quell-Origin für Navigation, Größen- und Anfragelimits, Socket-Timeout und Mindestabstand ergänzt.
- Begrenzte GET-Wiederholungen bei vorübergehenden Fehlern; keine automatischen Wiederholungen oder Weiterleitungen für Formular-POSTs. Fehlerausgaben enthalten keine Quelladressen oder Antworttexte.
- Abruf beobachteter Detailseiten mit Parser und Kalendervorschau verbunden; Ergebnisse bleiben unvollständige Vorschauen.
- Manuellen Flask-Befehl `source-check` und Anleitung für die Prüfung unter dem Dienstkonto ergänzt. Normale Webseitenaufrufe lösen keine Quellabrufe aus.
- README, Roadmap und Quellenanalyse nachgeführt. Automatische Studiengangs-/Wochennavigation und vollständige Semesterimporte bleiben offen.

**Prüfung:** 83 lokale Tests erfolgreich, einschließlich simulierter HTTP-Fehler, Weiterleitungen, Größenlimits, Abrufbudget, Parser-Anbindung, CLI und Versionsfooter; `git diff --check` ohne Fehler. Keine neuen Live-Abrufe oder Bereitstellung im LXC; Zielcontainer-Test des neuen Clients steht aus.

**Commit-Kurzbeschreibung:** Version 0.0.5 mit begrenztem Quellabruf und manuellem Verbindungstest ergänzen

## V0.0.4 – Kalendervorschau und Wochenabgleich

**Datum:** 2026-10-20

**Änderungen:**

- Version auf Userwunsch zentral auf `0.0.4` gesetzt; der gemeinsame Footer übernimmt sie.
- Erfolgreichen Website-Aufruf nach dem vorherigen Update durch den User bestätigt.
- Separate JSON-fähige Kalendervorschau ergänzt: wöchentliche Serien, vollständige Ausfalldaten, UTC-Zeitpunkte und lokale ISO-Wochen. Mehrdeutige Zeiten und ungeklärte Angaben führen zum Fehler statt zu Teilresultaten.
- Synthetisch geprüfte Einzel- und Blockregeln nur über explizite Rhythmuszuordnung zugelassen; Parser erhält einzelne Datumsangaben. Echte LSF-Sonderfälle bleiben zu verifizieren.
- Veranstaltungszuordnung über explizite Quell-, Studiengangs-, Prüfungsordnungs- und Semesterkennungen vorbereitet; keine Identität aus Titeln ableiten.
- Wochenabgleich erkennt fehlende, fehlerhafte, doppelte und unerwartete Wochen. Bestätigte leere Wochen von ungeprüften Leerantworten getrennt.
- Architekturentscheidung, README, Quellenanalyse und Roadmap aktualisiert. Zeitzonendaten für Windows als bedingte Abhängigkeit ergänzt.

**Prüfung:** 46 lokale Tests erfolgreich, einschließlich Versionsfooter, Zeitumstellung, Jahreswechsel, Ausfällen, Sonderregeln und fehlerhafter Wochenabdeckung; `git diff --check` ohne Fehler. Neue Fälle ausschließlich fiktiv; keine neuen Live-Abrufe oder Bereitstellung im LXC. Vollständiger Semesterimport, Navigation und echte Sonderfälle bleiben offen.

**Commit-Kurzbeschreibung:** Version 0.0.4 mit Kalendervorschau und sicherem Wochenabgleich ergänzen

## V0.0.3 – Quellenanalyse und erster Detailparser

**Datum:** 2026-10-20

**Änderungen:**

- Anwendungsversion auf Wunsch des Users zentral in `version.py` auf `0.0.3` gesetzt. Der Footer übernimmt die Version nach dem Deployment automatisch.
- Aktuelle Versionsangaben in Roadmap und Quellenanalyse aktualisiert. M0 bleibt in Bearbeitung.
- Feldstruktur zweier Veranstaltungsdetailseiten geprüft und eine ausschließlich fiktiv befüllte HTML-Testdatei aus der beobachteten Struktur erstellt.
- Detailparser mit Beautiful Soup ergänzt: Titel, optionale Metadaten und mehrere Terminserien lesen; unvollständige Seiten ablehnen; ungeprüfte Rhythmen, Ausfälle und fehlende Quellkennungen markieren. Keine ungeprüfte Erzeugung einzelner Kalendertermine.
- Parserentscheidung, Abhängigkeit und verbleibende Schritte für Sonderfälle und vollständigen Import dokumentiert.
- Eingabeprüfung von Installation und Update gegen führende/abschließende Leerzeichen und Wagenrückläufe gehärtet; ASCII-Locale festgelegt und ungültigen Git-Stand eindeutig ausgegeben. Der gemeldete Abbruch bei `main` ist mit unveränderter Eingabe lokal nicht reproduzierbar. 14 isolierte Bash-Eingabeprüfungen und beide Syntaxprüfungen erfolgreich; erneuter Zielcontainer-Test offen.

**Prüfung:** Versionswert, zentrale Einbindung im Footer und Dokumentationsangaben abgeglichen; `git diff --check` ohne Fehler. 22 lokale Tests erfolgreich. Detailparser zusätzlich an zwei Live-Seiten erfolgreich geprüft (eine bzw. zwei Terminserien), ohne Quelladressen oder Rohdaten zu speichern. Vollständiger Semesterimport und echte Sonderfälle bleiben offen; Änderungen noch nicht auf dem Server ausgerollt.

**Commit-Kurzbeschreibung:** Version 0.0.3 mit Detailparser ergänzen und Skripteingaben härten

## V0.0.2 – Debian-13-LXC-Installation

**Datum:** 2026-10-20

**Änderungen:**

- Anwendungsversion auf Wunsch des Users in `version.py` auf `0.0.2` gesetzt; der gemeinsame Footer übernimmt diesen Wert automatisch.
- Erstinstallationsskript für Debian-13-LXC mit Prüfung von Betriebssystem, root-Rechten, systemd, Installationszielen und lokalem Port ergänzt.
- Dienstkonto, virtuelle Python-Umgebung, Gunicorn, systemd-Dienst, Konfigurationsdatei und Datenverzeichnis vorgesehen. Vorhandene Installationen werden nicht überschrieben; Testausführung unter dem Dienstkonto und lokale HTTP-Prüfung integriert.
- Standard-Bind-Adresse auf `0.0.0.0` geändert; Abschlussmeldung zeigt die erkannten Container-IPv4-Webadressen mit dem gewählten Port. Anleitung für direkten Netzwerkzugriff und bestehende Installationen angepasst.
- Separates Git-Update-Skript ergänzt: Dienstkonfiguration erkennen, neuen Release und venv vorab testen, Konfiguration und Daten sichern, umschalten und bei Fehlern den bisherigen Anwendungspfad wiederherstellen. Konfiguration und Bind-Adresse bleiben erhalten; Update-Anleitung ergänzt.
- Erfolgreichen erneuten Betriebs- und Update-Test laut Nutzerbestätigung dokumentiert. M0 mit docs/source-analysis.md begonnen: Studiengangsuche und Planabruf ohne Login sowie Wochenwechsel einschließlich Jahreswechsel per HTTP geprüft. Semesterfilter können nicht zugeordnete Veranstaltungen ausblenden; verbleibende Prüfungen für Vollständigkeit und Sondertermine dokumentiert.
- Produktionsabhängigkeiten und LF-Zeilenenden für Shellskripte definiert.
- Installer an den Aufbau der NeoFab-ScanLab-Vorlage angepasst: interaktive Standardwerte, validierte Eingaben für Dienstnutzer, Installationspfad, Branch oder Tag und Bind-Adresse/Port, automatischer Clone des öffentlichen Projekt-Repositories sowie abschließende Übersicht mit installiertem Git-Commit.
- Download-Schnellstart ohne vorhandenen Checkout in docs/install.md und scripts/README.md ergänzt. Projektanweisungen um verbindliche Regeln für Git-basierte Installer und passende Anleitungen erweitert.
- `docs/install.md` mit Installation, Zugriff, Konfiguration, Betrieb und Fehlerbehandlung erstellt; README und Roadmap aktualisiert.

**Prüfung:** Bash-Syntax mit `bash -n` und Abbruch ohne root-Rechte geprüft; `git diff --check` ohne Fehler. Versionswert und Dokumentationsverweise abgeglichen. Die neue Webadressen-Ausgabe mit mehreren IPv4, Duplikaten, IPv6, lokalem Zugriff und fehlender IPv4 isoliert erfolgreich geprüft; der geänderte Netzwerkstandard wurde noch nicht erneut im LXC installiert. Laut vom User bereitgestelltem Installationsprotokoll vom 2026-10-20 ist die Debian-13-LXC-Erstinstallation für Commit `a58ee45b6495d130080b2d29e7330b8c6a4277b5` erfolgreich: Python 3.13.5, drei Tests bestanden, systemd-Dienst eingerichtet und lokale HTTP-Prüfung erfolgreich. Bind-Adresse `127.0.0.1:8000`. Der User bestätigt anschließend den laufenden Server und Zugriff im internen Netz. Update-Skript: Bash-Syntax, Abbruch ohne root und Rollback-Steuerung mit simulierten Systembefehlen geprüft (Vorbereitungsfehler, Umschaltfehler, Fehler vor Verschieben und erfolgreicher Abschluss). Erfolgreicher Update-Praxistest im LXC anschließend vom User bestätigt; tatsächlicher Fehlerfall mit Rollback im LXC noch offen. Prüfergebnis in Anleitung und Roadmap nachgeführt. Quellenanalyse: HTTP-200-Antworten für Einstieg, Suche, Plan und zwei Wochenwechsel beobachtet; keine vertraulichen Quelladressen oder Rohseiten im Repository abgelegt.

**Commit-Kurzbeschreibung:** Debian-LXC-Installation und Updates ergänzen sowie Quellenanalyse beginnen

## V0.0.1 – Konzept und Entwicklungsstart

**Datum:** 2026-10-20

**Änderungen:**

- Vorhandenes Projektbanner in die README eingebunden.
- Hinweise zur vertraulichen Quell-URL nach `docs/source-configuration.md` ausgelagert und in der README verlinkt.
- Aktuelle Anwendungsversion zentral als `__version__ = "0.0.1"` in `version.py` hinterlegt; dritte Versionsstelle vom User festgelegt.
- Projektanweisungen um zentrale Versionspflege, Versionsanzeige im Webseiten-Footer und Versionsvorschläge anhand der Roadmap ergänzt. Die dritte Versionsstelle bleibt dem User vorbehalten.
- Timeline einschließlich Commit-Kurzbeschreibung eingeführt und in der README verlinkt.
- Roadmap mit Projektgrundlagen, Meilensteinen M0 bis M5, Versionszielen und Abschlusskriterien erstellt und in der README verlinkt. Betrieb und Wiederherstellung als Voraussetzungen der MVP-Freigabe beschrieben.
- Projektanweisungen zur Timeline angepasst: sämtliche Änderungen derselben Version in einem Eintrag zusammenfassen und dessen Prüfstatus sowie Commit-Kurzbeschreibung fortschreiben. Bisherige Einträge für V0.0.1 zusammengeführt.

- Flask-App-Factory, Startseite mit Leerzustand und gemeinsames Layout mit Version aus version.py im Footer implementiert.
- Umgebungsbasierte Konfiguration, .env.example und Git-Ausschlüsse sowie getrennte Pakete für späteren Import, Parser, Speicherung und Scheduler angelegt. Keine Quellabrufe beim Start oder Seitenaufruf.
- Flask als Web-Abhängigkeit und pytest als Testwerkzeug aufgenommen; Tests für Start ohne Quelle, Versionsanzeige, vertrauliche Konfiguration und Stylesheet ergänzt. Installation und Testbefehle in der README dokumentiert.

**Prüfung:** Dokumentation mit README und Projektanweisungen abgeglichen; lokale Verweisziele sowie Versionswert geprüft; `git diff --check` ohne Fehler. Laufzeittests und Browserprüfung sind noch offen: Der vorhandene Windows-Python-Alias startet nicht (Fehler zur Anmeldesitzung); keine weitere Python-Installation gefunden. Die Abschlusskriterien des Projektgerüsts sind damit noch nicht vollständig verifiziert.

**Commit-Kurzbeschreibung:** Flask-Grundgerüst mit Versionsfooter, Konfiguration und Projektdokumentation anlegen
