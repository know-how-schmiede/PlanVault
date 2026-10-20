# Formularnavigation – V0.0.6

`backend.importer.forms.read_search_form` liest ein Suchformular anhand einer
expliziten Menge bereits bekannter Feldnamen. Genau ein Formular muss passen.
Die Feldnamen werden zur Laufzeit aus der Quellenanalyse bereitgestellt; echte
Quellparameter sind nicht im Code hinterlegt.

Das Ergebnis `SearchForm` enthält Ziel, Methode und Felder ausschließlich im
Arbeitsspeicher. Seine Textdarstellung enthält keine Ziele oder Feldwerte.
`submit` sendet über den vorhandenen `SourceClient`; Sitzungs-Cookies,
Abrufbudget, Mindestabstand und Origin-Prüfung gelten damit weiter.

Unterstützt werden:

- GET und URL-kodiertes POST, einschließlich relativer Formularziele.
- Versteckte Felder und wiederholte Feldnamen in ursprünglicher Reihenfolge.
- Textfelder, Textbereiche, einzelne und mehrfache Auswahlen.
- Erhalt aktivierter Checkbox-/Radiowerte und Weglassen deaktivierter Felder.
- Explizite Wahl einer beobachteten Submit-Schaltfläche.

Überschreibungen dürfen nur eindeutig benannte, editierbare Text- und
Auswahlfelder betreffen. Auswahlwerte müssen tatsächlich angeboten worden sein.
Versteckte Felder sind geschützt. GET ersetzt die Query des Formularziels durch
die Formulardaten; POST erhält die Ziel-Query und sendet die Daten im Body.

Loginfelder, fremde Ziele, mehrdeutige Formulare, Datei-Uploads, Fieldsets,
extern zugeordnete Controls, abweichende Zeichensätze und erkannte
JavaScript-Steuerung werden nicht automatisch interpretiert. Diese konservativen
Grenzen können erst nach Quellenprüfung erweitert werden.

## Prüfstand und nächster Schritt

Die Implementierung ist mit vollständig fiktiven Formularen getestet.
Es handelt sich noch nicht um eine automatisch funktionierende LSF-Suche.
Als Nächstes müssen die tatsächlich verwendeten Formulare, Feldnamen,
Suchschaltflächen und Trefferlinks im erlaubten Live-Ablauf zugeordnet werden.
Darauf folgen Studiengangs- und Wochennavigation sowie der Semesterabgleich.

Die Website bleibt unverändert bei der Startseite mit Versionsfooter; normale
Seitenaufrufe starten keine Navigation. Der manuelle
[Quelltest](source-check.md) bleibt für die Erreichbarkeitsprüfung verfügbar.
