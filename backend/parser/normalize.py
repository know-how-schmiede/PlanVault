"""Kalendervorschau aus Serien; kein Nachweis der Quellenvollständigkeit."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re
from zoneinfo import ZoneInfo

from backend.parser.course import CourseDetail


class NormalizationError(ValueError):
    """Nicht eindeutig normalisierbare Daten; ausschließlich bereinigte Meldungen."""

    def __init__(self, message, *, code="normalization_requires_review"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CourseContext:
    # Vom Abrufadapter verifizierte, opake Kennungen, niemals URLs.
    source_key: str
    study_key: str
    regulations_key: str
    semester: str
    source_key_verified: bool = False


@dataclass(frozen=True)
class Occurrence:
    course_key: str
    series_index: int
    starts_at: str
    ends_at: str
    local_date: str
    iso_year: int
    iso_week: int
    room: str | None
    instructor: str | None


@dataclass(frozen=True)
class CancelledDate:
    series_index: int
    local_date: str
    note: str | None


@dataclass(frozen=True)
class SeriesAnnotation:
    series_index: int
    kind: str
    text: str
    source_start_time: str | None = None
    source_end_time: str | None = None

@dataclass(frozen=True)
class CalendarPreview:
    course_key: str
    title: str
    semester: str
    occurrences: tuple[Occurrence, ...]
    review_reasons: tuple[str, ...]
    cancellations: tuple[CancelledDate, ...] = ()
    # Eine vollständige Semesterprüfung ist Aufgabe des Importers.
    complete: bool = False
    series_annotations: tuple[SeriesAnnotation, ...] = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def _identity(context: CourseContext) -> str:
    keys = (context.source_key, context.study_key, context.regulations_key)
    if any(not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key) for key in keys):
        raise NormalizationError("Verifizierte opake Quell- und Studiengangskennungen fehlen.")
    # Keine Titel, Räume oder Lehrpersonen in der Identität.
    payload = json.dumps((*keys, context.semester), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _has_date_reference(note: str | None) -> bool:
    if not note:
        return False
    return bool(
        re.search(r"(?<![\d.])\d{1,2}[./-]\d{1,2}[./-]\d{4}(?!\d)", note) or
        re.search(r"(?<![\d.])\d{1,2}[./-]\d{1,2}(?!\d)(?:\.(?!\d)|(?=[^\d./-]|$))", note)
    )

def _cancellations(text: str | None) -> dict[date, str | None]:
    if not text:
        return {}
    # Live beobachtet: mehrere Datum:-Einträge, teils ohne Hinweis.
    markers = list(re.finditer(r"(?<!\S)(\d{1,2}\.\d{1,2}\.\d{4}):", text))
    if markers:
        if markers[0].start() != 0 or len(markers) > 100 or len(text) > 10_000:
            raise NormalizationError("Ausfallangaben benötigen eine manuelle Prüfung.", code="unsupported_cancellation_format")
        result = {}
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
            note = text[marker.end():end].strip()
            if len(note) > 500:
                raise NormalizationError("Ausfallhinweis überschreitet die erlaubte Länge.")
            try:
                day = datetime.strptime(marker[1], "%d.%m.%Y").date()
            except ValueError:
                raise NormalizationError("Ausfallangabe enthält ein ungültiges Datum.") from None
            if day in result:
                raise NormalizationError("Mehrdeutige doppelte Ausfallangabe.")
            result[day] = note or None
        return result
    if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}(?:\s*[,;]\s*\d{1,2}\.\d{1,2}\.\d{4})*", text):
        raise NormalizationError("Ausfallangaben benötigen eine manuelle Prüfung.", code="unsupported_cancellation_format")
    try:
        return {datetime.strptime(part.strip(), "%d.%m.%Y").date(): None for part in re.split("[,;]", text)}
    except ValueError:
        raise NormalizationError("Ausfallangabe enthält ein ungültiges Datum.") from None


def _utc(day: date, clock, zone: ZoneInfo) -> datetime:
    naive = datetime.combine(day, clock)
    # Rückumrechnung erkennt sowohl die Zeitlücke als auch die doppelte Stunde.
    candidates = set()
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        if candidate.astimezone(zone).replace(tzinfo=None) == naive:
            candidates.add(candidate)
    if len(candidates) != 1:
        raise NormalizationError("Lokale Uhrzeit ist durch Zeitumstellung mehrdeutig oder ungültig.", code="ambiguous_local_time")
    return candidates.pop()


def _welcome_label(note):
    if note == "Einführungen studentischer Initiativen":
        return True
    speakers = re.fullmatch(
        r"Begrüßung ([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)*"
        r"(?:/[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)*)*)", note)
    reserved = {"entfällt", "verschoben", "abgesagt", "ausfall", "montag", "dienstag",
                "mittwoch", "donnerstag", "freitag", "samstag", "sonntag", "online", "raum"}
    return bool(speakers and not (set(re.split(r"[-/]", speakers[1].lower())) & reserved))


def normalize_course(
    course: CourseDetail, context: CourseContext, *,
    recurrence_rules: dict[str, str] | None = None,
) -> CalendarPreview:
    """Atomare Vorschau; unbekannte Angaben führen zum Fehler statt zu Teilterminen.

    Standardmäßig sind ``woch`` und ``Einzel`` belegt. Zusätzliche Quellrhythmen dürfen erst
    nach Prüfung explizit auf ``single`` oder ``daily`` abgebildet werden.
    Diese Optionen sind synthetisch getestet, keine Behauptung über LSF-Codes.
    """
    if course.semester != context.semester:
        raise NormalizationError("Semester der Zuordnung stimmt nicht überein.")
    key = _identity(context)
    rules = {"woch": "weekly", "Einzel": "single"} if recurrence_rules is None else dict(recurrence_rules)
    if any(value not in {"weekly", "single", "daily"} for value in rules.values()):
        raise NormalizationError("Unbekannte Wiederholungsregel.")
    if not course.series:
        raise NormalizationError("Veranstaltung enthält keine Terminserien.")
    review = set(course.review_reasons)
    # Fehlende Veranstaltungsnummer durch expliziten Adapter-Kontext ersetzt.
    review.discard("missing_source_identifier")
    # Die bereitgestellte Zuordnung wird hier nicht erneut an der Quelle geprüft.
    review.add("study_context_requires_verification" if context.source_key_verified
               else "source_context_requires_verification")
    occurrences = []
    cancellations = []
    annotations = []
    for index, series in enumerate(course.series):
        rule = rules.get(series.recurrence)
        if rule is None:
            raise NormalizationError("Rhythmus benötigt Prüfung.", code="unsupported_recurrence")
        if series.execution_note:
            raise NormalizationError("Durchführung oder Gruppierung benötigt Prüfung.", code="unsupported_execution_note")
        if series.timezone != "Europe/Berlin" or series.start_time >= series.end_time:
            raise NormalizationError("Ungültige Zeitzone oder Tageszeiten.")
        span = (series.valid_until - series.valid_from).days
        if not 0 <= span <= 370 or series.weekday not in range(7):
            raise NormalizationError("Terminzeitraum oder Wochentag ist ungültig.")
        if rule == "single" and span != 0:
            raise NormalizationError("Einzeltermin benötigt genau ein Datum.")
        effective_start, effective_end = series.start_time, series.end_time
        if series.note:
            exam = re.fullmatch(r"Die Klausur beginnt um (\d{1,2}:\d{2}) Uhr und endet um (\d{1,2}:\d{2}) Uhr\.", series.note)
            if series.note == "Vorlesung":
                kind = "teaching_format"
            elif _welcome_label(series.note):
                kind = "welcome_label"
                review.add("welcome_note_requires_review")
            elif series.note == "Nachholtermin" and rule == "single" and series.recurrence == "Einzel":
                kind = "makeup_label"
                review.add("replacement_reference_requires_review")
            elif re.fullmatch(r"(?:Labor|Raum) [A-Z]\d{1,2}\.\d{1,2}\.\d{2}", series.note):
                kind = "room_hint"
                review.add("room_note_requires_review")
            elif exam and rule == "single" and series.recurrence == "Einzel":
                try:
                    effective_start, effective_end = (datetime.strptime(t, "%H:%M").time() for t in exam.groups())
                except ValueError:
                    raise NormalizationError("Ungültige Uhrzeit im Klausurhinweis.", code="invalid_exam_time") from None
                if not series.start_time <= effective_start < effective_end <= series.end_time:
                    raise NormalizationError("Klausurzeiten liegen nicht innerhalb des Tabellenzeitraums.", code="exam_time_outside_series")
                kind = "exam_time"
                review.add("timing_note_requires_review")
            else:
                raise NormalizationError("Serienbemerkung ist noch nicht als Hinweis verifiziert.", code="unsupported_series_note")
            annotations.append(SeriesAnnotation(
                index, kind, series.note,
                series.start_time.isoformat() if kind == "exam_time" else None,
                series.end_time.isoformat() if kind == "exam_time" else None,
            ))
            review.add("notes_require_review")
        days = {
            series.valid_from + timedelta(days=offset)
            for offset in range(span + 1)
            if rule == "daily" or (series.valid_from + timedelta(days=offset)).weekday() == series.weekday
        }
        if not days:
            raise NormalizationError("Keine passenden Termine im Zeitraum.")
        cancelled = _cancellations(series.cancellation_text)
        if cancelled:
            review.add("cancellations_require_review")
        if any(_has_date_reference(note) for note in cancelled.values()):
            review.add("replacement_reference_requires_review")
        if rule != "weekly" and not (series.recurrence == "Einzel" and rule == "single"):
            review.add("special_recurrence_requires_verification")
        if not set(cancelled).issubset(days):
            raise NormalizationError("Ausfalldatum gehört nicht zur Terminserie.", code="cancellation_outside_series")
        cancellations.extend(CancelledDate(index, day.isoformat(), note) for day, note in sorted(cancelled.items()))
        zone = ZoneInfo(series.timezone)
        for day in sorted(days - set(cancelled)):
            start, end = _utc(day, effective_start, zone), _utc(day, effective_end, zone)
            if end <= start:
                raise NormalizationError("Zeitintervall ist nicht eindeutig.")
            year, week, _ = day.isocalendar()
            occurrences.append(Occurrence(
                key, index, start.isoformat(), end.isoformat(), day.isoformat(),
                year, week, series.room, series.instructor,
            ))
    occurrences.sort(key=lambda item: (item.starts_at, item.series_index))
    return CalendarPreview(key, course.title, course.semester, tuple(occurrences),
                           tuple(sorted(review)), tuple(cancellations),
                           series_annotations=tuple(annotations))
