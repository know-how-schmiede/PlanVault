"""Begrenzte Detailstichprobe aus beobachteten Planlinks, ohne Veröffentlichung."""

from dataclasses import dataclass, field
import hashlib
import re

from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.navigation import _page, _caption
from backend.importer.forms import FormNavigationError
from backend.parser import (
    CalendarPreview, CourseContext, NormalizationError, SourceParseError,
    normalize_course, parse_course_detail,
)


class DetailImportError(ValueError):
    """Bereinigter Fehler; keine Teilstichprobe als erfolgreich zurückgeben."""


@dataclass(frozen=True)
class CourseReference:
    # Hash dient nur der Zuordnung innerhalb dieses Prüflaufs, nicht als Archiv-ID.
    key: str
    location: str = field(repr=False)
    caption: str = field(repr=False)
    block_count: int


@dataclass(frozen=True)
class DetailResult:
    reference_key: str
    series_count: int
    status: str
    preview: CalendarPreview | None = field(repr=False)

    @property
    def requires_review(self) -> bool:
        return self.status != "preview" or bool(
            self.preview and set(self.preview.review_reasons) - {"source_context_requires_verification"}
        )


@dataclass(frozen=True)
class DetailSample:
    reference_count: int
    block_count: int
    details: tuple[DetailResult, ...]
    complete: bool = False

    @property
    def unchecked_count(self):
        return self.reference_count - len(self.details)


def merge_course_references(groups: tuple[tuple[CourseReference, ...], ...]) -> tuple[CourseReference, ...]:
    """Bereits geprüfte Verweise ohne erneute Abrufe wochenübergreifend vereinen."""
    merged = {}
    for group in groups:
        for reference in group:
            previous = merged.get(reference.location)
            if previous and (previous.caption != reference.caption or previous.key != reference.key):
                raise DetailImportError("Widersprüchliche Detailzuordnung zwischen Wochen.")
            merged[reference.location] = CourseReference(
                reference.key, reference.location, reference.caption,
                reference.block_count + (previous.block_count if previous else 0),
            )
    if sum(reference.block_count for reference in merged.values()) > 5000:
        raise DetailImportError("Zu viele Veranstaltungsblöcke.")
    return tuple(merged.values())


def validate_detail_context(semester: str, study_key: str, regulations_key: str, limit: int):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10:
        raise DetailImportError("Detailgrenze muss zwischen eins und zehn liegen.")
    if (not isinstance(semester, str) or not semester.strip() or
            any(not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", key)
                for key in (study_key, regulations_key))):
        raise DetailImportError("Semester und opake Studiengangs-/Prüfungsordnungskennungen erforderlich.")


def collect_course_references(client: SourceClient, documents: tuple[SourceDocument, ...]) -> tuple[CourseReference, ...]:
    """Gleiche absolute Linkziele über alle übergebenen Pläne einmal aufnehmen.

    Unterschiedliche URLs werden nicht anhand von Titeln zusammengeführt.
    Sitzungsabhängige URL-Varianten bleiben daher bewusst unterschiedliche Ziele.
    """
    if not documents or len(documents) > 54:
        raise DetailImportError("Ungültige Anzahl von Planantworten.")
    references = {}
    block_count = 0
    for document in documents:
        try:
            soup = _page(document)
            blocks = soup.select("td.plan5a")
            if not blocks:
                raise DetailImportError("Keine bekannten Veranstaltungsblöcke; kein bestätigter leerer Plan.")
            for block in blocks:
                block_count += 1
                if block_count > 5000:
                    raise DetailImportError("Zu viele Veranstaltungsblöcke.")
                table = block.find_parent("table")
                if table is None:
                    raise DetailImportError("Veranstaltungsblock ohne geprüfte Tabellenstruktur.")
                rows = [row for row in table.find_all("tr") if row.find_parent("table") is table]
                links = block.find_all("a", href=True)
                if (len(rows) != 8 or block.find_parent("tr") is not rows[0] or
                        len(links) != 1 or links[0].has_attr("onclick") or not _caption(links[0])):
                    raise DetailImportError("Unbekannte oder mehrdeutige Veranstaltungsverknüpfung.")
                target = client.resolve(links[0]["href"], relative_to=document.location)
                caption = _caption(links[0])
                previous = references.get(target)
                if previous is not None and previous.caption != caption:
                    raise DetailImportError("Dasselbe Detailziel hat widersprüchliche Beschriftungen.")
                references[target] = CourseReference(
                    hashlib.sha256(target.encode("utf-8")).hexdigest(), target, caption,
                    previous.block_count + 1 if previous else 1,
                )
        except (FormNavigationError, SourceFetchError):
            raise DetailImportError("Planstruktur oder Detailziel konnte nicht sicher zugeordnet werden.") from None
    return tuple(references.values())


def fetch_detail_sample(client: SourceClient, references: tuple[CourseReference, ...], *,
                        semester: str, study_key: str, regulations_key: str,
                        limit: int = 2) -> DetailSample:
    """Maximal zehn eindeutige Detailziele; bei Abruf-/Parserfehlern kein Teilergebnis."""
    validate_detail_context(semester, study_key, regulations_key, limit)
    if not references or len({ref.location for ref in references}) != len(references):
        raise DetailImportError("Ungültige oder doppelte Detailauswahl.")
    details = []
    for reference in references[:limit]:
        try:
            document = client.fetch(reference.location)
            course = parse_course_detail(document.html, expected_semester=semester)
        except (SourceFetchError, SourceParseError):
            raise DetailImportError("Detailstichprobe abgebrochen: Abruf, Semester oder Parserstruktur ungeklärt.") from None
        try:
            preview = normalize_course(course, CourseContext(reference.key, study_key, regulations_key, semester))
            status = "preview"
        except NormalizationError:
            # Ein korrekt gelesenes Detail kann noch nicht interpretierte Sonderfälle enthalten.
            preview, status = None, "normalization_requires_review"
        details.append(DetailResult(reference.key, len(course.series), status, preview))
    return DetailSample(len(references), sum(ref.block_count for ref in references), tuple(details))
