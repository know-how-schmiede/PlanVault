"""Beobachtete Wochenauswahl und struktureller Abgleich, kein Semesterimport."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import re

from backend.importer.coverage import Coverage, WeekResult, check_week_coverage
from backend.importer.forms import FormNavigationError, SearchForm, read_search_form
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.navigation import _page, _caption


_WEEK = re.compile(r"Woche:\s*(\d{1,2})\s+(\d{1,2}\.\d{1,2}\.\d{4})\s*-+\s*(\d{1,2}\.\d{1,2}\.\d{4})")
_DAY = re.compile(r"(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)\s+(\d{1,2}\.\d{1,2}\.\d{4})(?:\s+(.+))?")
_DAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


@dataclass(frozen=True)
class WeekChoice:
    start: date
    end: date
    value: str = field(repr=False)

    @property
    def key(self):
        return self.start.isocalendar()[:2]


@dataclass(frozen=True)
class WeekMenu:
    choices: tuple[WeekChoice, ...]
    selected: tuple[int, int] | None
    form: SearchForm = field(repr=False)
    field_name: str = field(repr=False)
    button: tuple[str, str] = field(repr=False)


@dataclass(frozen=True)
class WeekAudit:
    results: tuple[WeekResult, ...]
    coverage: Coverage
    # Auch korrekte Wochenantworten beweisen keine vollständigen Veranstaltungsdaten.
    complete: bool = False


def read_week_menu(document: SourceDocument) -> WeekMenu:
    soup = _page(document)
    candidates = [select for select in soup.find_all("select")
                  if any(_caption(option).startswith("Woche:") for option in select.find_all("option"))]
    if len(candidates) != 1:
        raise FormNavigationError("Wochenauswahl fehlt oder ist mehrdeutig.")
    select = candidates[0]
    if not select.get("name") or select.has_attr("disabled") or select.has_attr("multiple"):
        raise FormNavigationError("Wochenauswahl ist nicht bedienbar.")
    choices, selected = [], []
    all_selected = select.find_all("option", selected=True)
    if len(all_selected) != 1:
        raise FormNavigationError("Aktuelle Ansicht ist nicht eindeutig ausgewählt.")
    for option in select.find_all("option"):
        caption = _caption(option)
        if not caption.startswith("Woche:"):
            continue
        match = _WEEK.fullmatch(caption)
        if not match or not option.get("value") or option.has_attr("disabled"):
            raise FormNavigationError("Unbekannte oder deaktivierte Wochenangabe.")
        try:
            number = int(match[1])
            start, end = (datetime.strptime(value, "%d.%m.%Y").date() for value in match.groups()[1:])
        except ValueError:
            raise FormNavigationError("Ungültiges Datum in der Wochenauswahl.") from None
        if start.weekday() != 0 or end != start + timedelta(days=6) or start.isocalendar().week != number:
            raise FormNavigationError("Wochennummer und Datumsbereich stimmen nicht überein.")
        choice = WeekChoice(start, end, option["value"])
        choices.append(choice)
        if option.has_attr("selected"):
            selected.append(choice.key)
    if (not choices or len(choices) > 54 or
            len({choice.key for choice in choices}) != len(choices) or
            len({choice.value for choice in choices}) != len(choices)):
        raise FormNavigationError("Wochenliste ist leer, zu groß oder mehrdeutig.")
    form = read_search_form(document, required_fields={select["name"]})
    buttons = {button for button in form.buttons if button[1] == "anzeigen"}
    if len(buttons) != 1:
        raise FormNavigationError("Schaltfläche für den Wochenwechsel fehlt oder ist mehrdeutig.")
    return WeekMenu(tuple(sorted(choices, key=lambda choice: choice.start)),
                    selected[0] if selected else None, form, select["name"], buttons.pop())


def inspect_week(document: SourceDocument, expected: WeekChoice) -> WeekResult:
    menu = read_week_menu(document)
    if menu.selected != expected.key:
        raise FormNavigationError("Quelle hat die angeforderte Woche nicht übernommen.")
    soup = _page(document)
    days = []
    notices = False
    for header in soup.find_all("th"):
        text = _caption(header)
        if not text.startswith(_DAYS):
            continue
        match = _DAY.fullmatch(text)
        if not match:
            raise FormNavigationError("Unbekannte Tagesüberschrift.")
        try:
            day = datetime.strptime(match[2], "%d.%m.%Y").date()
        except ValueError:
            raise FormNavigationError("Ungültiges Tagesdatum.") from None
        if _DAYS[day.weekday()] != match[1]:
            raise FormNavigationError("Tagesname und Datum stimmen nicht überein.")
        days.append(day)
        notices = notices or bool(match[3])
    expected_days = [expected.start + timedelta(days=offset) for offset in range(5)]
    # Bisher live beobachtet: genau Montag bis Freitag, kein Wochenendnachweis.
    if days != expected_days:
        raise FormNavigationError("Sichtbare Tagesdaten passen nicht zur angeforderten Woche.")
    status = "notes_require_review" if notices else ("ok" if soup.select("td.plan5a") else "empty_unverified")
    return WeekResult(*expected.key, status)


def audit_weeks(client: SourceClient, document: SourceDocument, *, start: date, end: date,
                requested: tuple[tuple[int, int], ...]) -> WeekAudit:
    """Explizit ausgewählte Wochen sequenziell prüfen; beim ersten Fehler abbrechen.

    Der Zeitraum ist eine unabhängige Erwartung des Aufrufers. Nicht abgerufene
    Wochen bleiben fehlend, auch wenn sie im Auswahlmenü angeboten wurden.
    """
    check_week_coverage(start, end, [])
    if not requested or len(requested) > 54 or len(set(requested)) != len(requested):
        raise FormNavigationError("Wochenauftrag ist leer, zu groß oder enthält Duplikate.")
    initial = read_week_menu(document)
    available = {choice.key: choice for choice in initial.choices}
    for key in requested:
        if key not in available:
            raise FormNavigationError("Angeforderte Woche wird nicht angeboten.")
        if available[key].end < start or available[key].start > end:
            raise FormNavigationError("Angeforderte Woche liegt außerhalb des Prüfzeitraums.")
    results = []
    for key in requested:
        try:
            current = read_week_menu(document)
            if tuple(choice.key for choice in current.choices) != tuple(choice.key for choice in initial.choices):
                raise FormNavigationError("Wochenangebot hat sich während der Prüfung geändert.")
            choice = next(choice for choice in current.choices if choice.key == key)
            document = current.form.submit(client, values={current.field_name: (choice.value,)},
                                           button=current.button)
            result = inspect_week(document, choice)
            # Auch in der letzten Antwort muss das Wochenangebot unverändert sein.
            if tuple(c.key for c in read_week_menu(document).choices) != tuple(c.key for c in initial.choices):
                raise FormNavigationError("Wochenangebot hat sich während der Prüfung geändert.")
            results.append(result)
            if result.status != "ok":
                break
        except (FormNavigationError, SourceFetchError):
            results.append(WeekResult(*key, "failed"))
            break
    return WeekAudit(tuple(results), check_week_coverage(start, end, results))
