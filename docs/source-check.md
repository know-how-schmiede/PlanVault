# Quellzugriff prüfen

Ab Version 0.0.5 steht ein manueller Verbindungstest zur Verfügung. Er lädt die
konfigurierte Einstiegsseite und prüft auf Formular- und Auswahlfelder. Eine
erkannte Anmeldeseite wird abgelehnt. Es werden keine Quelladressen, Antworttexte
oder Cookies ausgegeben oder gespeichert.

Der Test bestätigt **keinen erfolgreichen Import**. Auch eine andere Seite mit
Formular und Auswahlfeldern kann diese einfache Strukturprüfung erfüllen.
Studiengang, Semester, Quellkennungen und vollständiger Semesterumfang müssen
separat verifiziert werden.

## Im Debian-LXC

Zuerst Version 0.0.5 veröffentlichen und mit dem vorhandenen Update-Skript
installieren. Die vertrauliche Adresse muss in der bereits vorgesehenen
Laufzeitkonfiguration `/etc/wi-planarchiv/app.env` unter `LSF_BASE_URL` gesetzt sein.
Die Datei nur lokal bearbeiten; ihren Inhalt nicht in Chat, Git oder Logs kopieren.
Siehe [Quellkonfiguration](source-configuration.md).

Als root mit den Standardpfaden und dem Standard-Dienstkonto:

```bash
systemd-run --unit=wi-planarchiv-source-check --wait --pipe --collect \
  --property=User=wi-planarchiv \
  --property=Group=wi-planarchiv \
  --property=WorkingDirectory=/opt/wi-planarchiv \
  --property=EnvironmentFile=/etc/wi-planarchiv/app.env \
  /opt/wi-planarchiv/.venv/bin/python -m flask --app backend source-check
```

Bei abweichender Installation Benutzer, Gruppe und Pfade anpassen. Die temporäre
Prüfung verwendet die Konfiguration unter dem Dienstkonto und verändert den
laufenden Webdienst nicht. Kein Neustart des Webdienstes ist für diesen Test nötig.

Erwartete erfolgreiche Ausgabe:

```text
Einstiegsseite erreichbar; Formular und Auswahlfelder erkannt.
Kein Import durchgeführt. Studiengang, Semester und Vollständigkeit sind noch ungeprüft.
```

Bei fehlender Konfiguration, Netzwerkfehlern, Loginseiten oder abweichender Struktur
endet der Befehl mit einem Fehlerstatus und einer bereinigten Meldung.

## Lokal

In einer aktivierten virtuellen Umgebung und mit bereits gesetztem `LSF_BASE_URL`:

```bash
python -m flask --app backend source-check
```

Der Test lädt nur den Einstieg, ohne automatische Wiederholungen und mit einem
Budget von fünf HTTP-Anfragen einschließlich Weiterleitungen. Die allgemeine
Client-Sitzung hat standardmäßig 20 Anfragen, zehn Sekunden Socket-Timeout,
mindestens eine Sekunde Abstand und maximal zwei Wiederholungen für GET bei
vorübergehenden Verbindungsfehlern oder HTTP 429/502/503/504. Formular-POSTs werden
nicht wiederholt oder automatisch weitergeleitet. Antworten sind auf zwei MB
begrenzt. Nur HTTPS und derselbe Host/Port wie in der Konfiguration sind erlaubt.

## Entwicklungsstand

`fetch_course_preview` verbindet einen zuvor beobachteten Detaillink mit
Detailparser und Normalisierung. Cookies werden nur in der laufenden Sitzung
gehalten und beim Schließen gelöscht. Der Aufrufer muss verifizierte
Studiengangs-, Prüfungsordnungs- und Quellkennungen bereitstellen.

Die Studiengangsnavigation ist ab V0.0.7 implementiert und für einen Studiengang
live geprüft. Wochenabrufe und der Abgleich eines gesamten Semesters fehlen. Die Website
zeigt weiterhin die Startseite; ein normaler Seitenaufruf startet keinen Abruf.
Der Client ist mit simulierten Antworten und dem Studiengangsablauf live getestet. Ein Live-Test der neuen
Implementierung im Zielcontainer steht aus.

## Studiengangsnavigation prüfen (ab V0.0.7)

`source-plan-check` verbindet Einstieg, Suche, exakte Trefferwahl und
Auswahlbestätigung. Suchtext und vollständige Trefferbeschriftung einschließlich
Prüfungsordnung müssen explizit angegeben werden. Mehrere unterschiedliche Ziele
mit gleichem Titel führen zum Abbruch. Leerzeichen in der Beschriftung werden
vereinheitlicht.

Lokal, mit gesetztem `LSF_BASE_URL`:

```bash
python -m flask --app backend source-plan-check \
  --query "Fiktiv" --title "Fiktives Studium (DEMO-PO)"
```

Die Angaben sind **fiktive Platzhalter** und durch die gewünschte, tatsächlich
sichtbare Auswahl zu ersetzen. Im LXC den oben beschriebenen `systemd-run`-Befehl
verwenden und dessen abschließendes `source-check` durch
`source-plan-check --query "SUCHTEXT" --title "EXAKTE TREFFERBESCHRIFTUNG"` ersetzen.
Vorher Version 0.0.7 auf GitHub veröffentlichen und installieren.

Der Befehl erlaubt höchstens zehn HTTP-Anfragen einschließlich Weiterleitungen,
ohne automatische Wiederholungen. Er meldet nur die Anzahl erkannter Blöcke des
bekannten Veranstaltungsmusters und erstellt keinen Import oder Archivstand.
Eine Antwort ohne bekannte Blöcke wird ausdrücklich nicht als gültiger leerer
Plan bestätigt. Voreinstellungen für Semester und Filter werden aus der Quelle
übernommen; deren fachliche Eignung und Vollständigkeit sind damit nicht belegt.
