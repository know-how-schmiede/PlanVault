# Veranstaltungskennungen ab V0.0.12

Die Detailstichprobe und der gemeinsame Import-Prüflauf können Veranstaltungen
über eine ausdrücklich konfigurierte numerische Quellkennung zuordnen.
Titel, Raum, Sitzungswerte und Reihenfolge der übrigen URL-Parameter bestimmen
diese Identität nicht. Änderungen solcher Angaben erzeugen dadurch keine neue
Veranstaltungskennung.

## Lokale Konfiguration

In der vertraulichen Laufzeitkonfiguration außerhalb des Checkouts
(bei Standardinstallation `/etc/wi-planarchiv/app.env`) ergänzen:

- `LSF_ID_PARAMETER`: der durch Quellenanalyse bestätigte Parametername des
  Veranstaltungsdatensatzes. Kein automatisches Raten anhand numerischer Werte.
- `LSF_ID_NAMESPACE`: ein selbst gewählter, dauerhaft gleicher lokaler Name aus
  Buchstaben, Ziffern, Unterstrich oder Bindestrich.

Beide Werte bleiben im Repository leer. Den tatsächlichen Parameternamen nur
lokal anhand der geprüften Detailverknüpfung eintragen, niemals in Dokumentation,
Issues oder Logs kopieren. Für manuelle Prüfungen dieselbe Konfigurationsdatei
wie beim [Quelltest](source-check.md) laden.

Fehlen beide Werte, bleibt die bisherige Zuordnung innerhalb eines Prüflaufs
aktiv. Fehlt nur einer, wird die Konfiguration abgelehnt. Bei aktivierter
Zuordnung führen fehlende, doppelte oder ungültige Kennungen zum Abbruch;
es gibt keinen stillen Rückfall auf Link- oder Titelvergleich.

## Identität und Grenzen

Ein SHA-256-Schlüssel umfasst Formatversion, lokalen Namensraum, Quellhost,
HTTPS-Port und numerische Datensatzkennung. Der Normalizer ergänzt Studiengang,
Prüfungsordnung und Semester. Änderungen des Namensraums verändern die Schlüssel
und müssen vor einer späteren Archivmigration bewusst geplant werden.

Mehrere Sitzungslinks derselben Kennung werden zusammengeführt. Widersprüchliche
Titel innerhalb desselben Prüflaufs werden abgelehnt; Titeländerungen zwischen
getrennten Läufen ändern die Kennung nicht.

Der JSON-Bericht verwendet jetzt `schema_version=2` und `identity_mode`:
`run` für die bisherige laufbezogene Zuordnung, `configured` für eine aktivierte
Kennungsregel. Der Modus bestätigt die Konfiguration, nicht den Erfolg des
Imports. Parameternamen, Namensraum, Quellwerte und Schlüssel erscheinen nicht
im Bericht.

Die Zuordnung von Studiengang und Prüfungsordnung bleibt prüfpflichtig:
`study_context_unverified` ersetzt bei konfigurierter Kennung den allgemeinen
Blocker `source_identity_unverified`. Semesterumfang, Sonderfälle und vollständige
Detailerfassung bleiben eigenständige Voraussetzungen. `complete` und `published`
bleiben `false`; Speicherung und Stundenplananzeige folgen erst danach.

## Nachweis

Am 2026-10-20 wurden 47 Detailziele in unabhängigen Sitzungen verglichen.
Die numerischen Kennungen blieben gleich. Dies belegt die beobachtete
Sitzungsunabhängigkeit, keine garantierte Lebensdauer oder Wiederverwendungspolitik
der Quelle. Rohseiten, echte Parameternamen und Quellwerte wurden nicht gespeichert.
Lokale Tests verwenden ausschließlich fiktive Kennungen.
