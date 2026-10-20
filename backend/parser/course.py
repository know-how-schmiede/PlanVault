"""Parser für die geprüfte Veranstaltungsdetailtabelle.

Terminserien werden erhalten, aber noch nicht in einzelne Termine expandiert.
Dieser Parser bestätigt keine vollständige Erfassung eines Studiengangs.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
import re

from bs4 import BeautifulSoup, Tag


class SourceParseError(ValueError):
    """Quellstruktur ist unbekannt oder unvollständig; Meldungen enthalten keine Quelldaten."""


@dataclass(frozen=True)
class ScheduleSeries:
    weekday: int  # Montag = 0, Sonntag = 6
    start_time: time
    end_time: time
    valid_from: date
    valid_until: date
    recurrence: str
    room: str | None
    instructor: str | None
    execution_note: str | None
    note: str | None
    cancellation_text: str | None
    timezone: str = "Europe/Berlin"


@dataclass(frozen=True)
class CourseDetail:
    source_identifier: str | None
    title: str
    description: str | None
    event_type: str
    semester: str
    series: tuple[ScheduleSeries, ...]
    review_reasons: tuple[str, ...]


_WEEKDAYS = {day: number for number, day in enumerate(("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"))}
_HEADERS = ("Tag", "Zeit", "Rhythmus", "Dauer", "Raum", "Lehrperson", "Durchf.", "Bemerkung", "fällt aus am")
_TIME_RANGE = re.compile(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})")
_DATE_RANGE = re.compile(r"(\d{1,2}\.\d{1,2}\.\d{4})\s*[-–]\s*(\d{1,2}\.\d{1,2}\.\d{4})")


def _text(cell: Tag) -> str:
    value = " ".join(cell.get_text(" ", strip=True).split())
    # Freitext kann ausgeschriebene Adressen enthalten; Linkziele werden nie gelesen.
    return re.sub(r"https?://\S+", "[Adresse entfernt]", value, flags=re.IGNORECASE)


def _rows(table: Tag) -> list[Tag]:
    return [row for row in table.find_all("tr") if row.find_parent("table") is table]


def _metadata(table: Tag) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _rows(table):
        label = None
        for cell in row.find_all(["th", "td"], recursive=False):
            if cell.name == "th":
                label = _text(cell)
            elif label:
                value = _text(cell)
                if label in result and result[label] != value:
                    raise SourceParseError("Widersprüchliche Veranstaltungsangaben.")
                result[label] = value
                label = None
    for field in ("Veranstaltungsart", "Semester"):
        if not result.get(field):
            raise SourceParseError("Erforderliche Veranstaltungsangaben fehlen.")
    return result


def _series(cells: dict[str, str]) -> ScheduleSeries:
    weekday = cells["Tag"].removesuffix(".")
    times = _TIME_RANGE.fullmatch(cells["Zeit"])
    dates = _DATE_RANGE.fullmatch(cells["Dauer"])
    if weekday not in _WEEKDAYS or times is None or dates is None or not cells["Rhythmus"]:
        raise SourceParseError("Terminangaben sind unvollständig oder noch nicht unterstützt.")
    try:
        start_time, end_time = (datetime.strptime(value, "%H:%M").time() for value in times.groups())
        valid_from, valid_until = (datetime.strptime(value, "%d.%m.%Y").date() for value in dates.groups())
    except ValueError:
        raise SourceParseError("Termin enthält ein ungültiges Datum oder eine ungültige Uhrzeit.") from None
    if start_time >= end_time or valid_from > valid_until:
        raise SourceParseError("Terminintervall ist ungültig oder überschreitet eine Tagesgrenze.")
    if (valid_until - valid_from).days < (_WEEKDAYS[weekday] - valid_from.weekday()) % 7:
        raise SourceParseError("Wochentag liegt nicht im angegebenen Zeitraum.")
    return ScheduleSeries(
        weekday=_WEEKDAYS[weekday], start_time=start_time, end_time=end_time,
        valid_from=valid_from, valid_until=valid_until, recurrence=cells["Rhythmus"],
        room=cells["Raum"] or None, instructor=cells["Lehrperson"] or None,
        execution_note=cells["Durchf."] or None, note=cells["Bemerkung"] or None,
        cancellation_text=cells["fällt aus am"] or None,
    )


def parse_course_detail(html: str, *, expected_semester: str | None = None) -> CourseDetail:
    """Geprüfte Detailstruktur lesen; unbekannte Zeilen niemals überspringen.

    ``review_reasons`` markieren ungeprüfte Rhythmen, Ausnahmen oder Gruppierungen.
    Auch ohne diese Hinweise ist das Ergebnis keine vollständige Semesterplanung.
    """
    if not isinstance(html, str) or not html.strip() or len(html) > 2_000_000:
        raise SourceParseError("Quelldokument fehlt oder überschreitet die erlaubte Größe.")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    if soup.find("input", attrs={"type": re.compile("^password$", re.IGNORECASE)}):
        raise SourceParseError("Anmeldeseite statt Veranstaltungsdaten erhalten.")
    tables = soup.find_all("table")
    metadata_tables = [t for t in tables if {"Veranstaltungsnummer", "Langtext"}.issubset(
        {_text(th) for th in t.find_all("th") if th.find_parent("table") is t}
    )]
    if len(metadata_tables) != 1:
        raise SourceParseError("Eindeutige Veranstaltungsdetailstruktur fehlt.")
    metadata = _metadata(metadata_tables[0])
    headings = soup.find_all("h3")
    if len(headings) != 1 or not _text(headings[0]):
        raise SourceParseError("Eindeutiger Veranstaltungstitel fehlt.")
    if expected_semester is not None and metadata["Semester"] != expected_semester:
        raise SourceParseError("Hochschulsemester entspricht nicht der angeforderten Auswahl.")

    parsed: list[ScheduleSeries] = []
    review: set[str] = set()
    if not metadata.get("Veranstaltungsnummer"):
        review.add("missing_source_identifier")
    schedule_count = 0
    for table in tables:
        rows = _rows(table)
        heading_rows = [r for r in rows if r.find("th", recursive=False)]
        all_headers = {_text(th) for r in heading_rows for th in r.find_all("th", recursive=False)}
        if "Zeit" not in all_headers and "Dauer" not in all_headers:
            continue
        if len(heading_rows) != 1 or not set(_HEADERS).issubset(all_headers):
            raise SourceParseError("Unbekannte oder unvollständige Termintabelle.")
        headers = [_text(th) for th in heading_rows[0].find_all("th", recursive=False)]
        if len(headers) != len(set(headers)):
            raise SourceParseError("Mehrdeutige Spalten in der Termintabelle.")
        if any(h and h not in _HEADERS for h in headers):
            raise SourceParseError("Zusätzliche unbekannte Terminspalte.")
        schedule_count += 1
        table_series = 0
        for row in rows:
            if row is heading_rows[0]:
                continue
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells:
                continue
            if len(cells) != len(headers) or any(
                c.get("colspan", "1") != "1" or c.get("rowspan", "1") != "1" or c.find("table")
                for c in cells
            ):
                raise SourceParseError("Zusammengefasste oder unbekannte Terminzeile.")
            series = _series(dict(zip(headers, map(_text, cells))))
            parsed.append(series)
            table_series += 1
            if series.recurrence != "woch":
                review.add("unverified_recurrence")
            if series.cancellation_text:
                review.add("cancellations_require_review")
            if series.note or series.execution_note:
                review.add("notes_require_review")
        if not table_series:
            raise SourceParseError("Leere Termintabelle ist noch nicht als gültiger Plan verifiziert.")
    if not parsed:
        raise SourceParseError("Keine geprüften Terminzeilen gefunden.")
    if schedule_count > 1:
        review.add("multiple_schedule_tables_require_review")
    return CourseDetail(
        source_identifier=metadata.get("Veranstaltungsnummer") or None, title=_text(headings[0]),
        description=metadata.get("Langtext") or None,
        event_type=metadata["Veranstaltungsart"], semester=metadata["Semester"],
        series=tuple(parsed), review_reasons=tuple(sorted(review)),
    )
