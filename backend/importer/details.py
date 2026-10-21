"""Begrenzte Detailstichprobe aus beobachteten Planlinks, ohne Veröffentlichung."""

from dataclasses import dataclass, field
import hashlib
import re

from backend.importer.structure import COURSE_BLOCK_SELECTOR
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.navigation import _page, _caption
from backend.importer.forms import FormNavigationError
from backend.importer.identity import SourceIdentityPolicy, SourceIdentityError
from backend.parser import (
    CalendarPreview, CourseContext, CourseDetail, NormalizationError, SourceParseError,
    normalize_course, parse_course_detail,
)


class DetailImportError(ValueError):
    """Bereinigter Fehler; keine Teilstichprobe als erfolgreich zurückgeben."""


@dataclass(frozen=True)
class CourseReference:
    # Scope unterscheidet Lauf-Hash und ausdrücklich konfigurierte Quellkennung.
    key: str
    location: str = field(repr=False)
    caption: str = field(repr=False)
    block_count: int
    identity_scope: str = "run"


@dataclass(frozen=True)
class DetailResult:
    reference_key: str
    series_count: int
    status: str
    preview: CalendarPreview | None = field(repr=False)
    unresolved_course: CourseDetail | None = field(default=None, repr=False)
    blocking_reason: str | None = None
    source_course: CourseDetail | None = field(default=None, repr=False)

    @property
    def requires_review(self) -> bool:
        return self.status != "preview" or bool(
            self.preview and set(self.preview.review_reasons) -
            {"source_context_requires_verification", "study_context_requires_verification"}
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

    def normalization_summary(self):
        """Technische Abbrüche von erzeugten, fachlich prüfpflichtigen Vorschauen trennen."""
        return {
            "preview_count": sum(d.preview is not None for d in self.details),
            "blocked_count": sum(d.preview is None for d in self.details),
            "review_preview_count": sum(d.preview is not None and d.requires_review for d in self.details),
        }

    def review_summary(self):
        """Nur feste Codes und laufbezogene Nummern; keine Quell- oder Freitexte."""
        counts = {}
        details = []
        for index, detail in enumerate(self.details, 1):
            reasons = ([detail.blocking_reason or "normalization_requires_review"]
                       if detail.preview is None else sorted(set(detail.preview.review_reasons)))
            for reason in reasons:
                counts[reason] = counts.get(reason, 0) + 1
            if reasons:
                details.append({"detail_number": index, "blocked": detail.preview is None,
                                "reasons": reasons})
        return {"reason_counts": dict(sorted(counts.items())), "details": details}


def merge_course_references(groups: tuple[tuple[CourseReference, ...], ...]) -> tuple[CourseReference, ...]:
    """Bereits geprüfte Verweise ohne erneute Abrufe wochenübergreifend vereinen."""
    merged = {}
    for group in groups:
        for reference in group:
            identity = (reference.identity_scope, reference.key)
            previous = merged.get(identity)
            if previous and (previous.caption != reference.caption or previous.key != reference.key):
                raise DetailImportError("Widersprüchliche Detailzuordnung zwischen Wochen.")
            merged[identity] = CourseReference(
                reference.key, reference.location, reference.caption,
                reference.block_count + (previous.block_count if previous else 0),
                reference.identity_scope,
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


def collect_course_references(client: SourceClient, documents: tuple[SourceDocument, ...], *,
                              identity_policy: SourceIdentityPolicy | None = None) -> tuple[CourseReference, ...]:
    """Nach konfigurierter Kennung, sonst nach absolutem Linkziel deduplizieren.

    Titel sind niemals Identität; widersprüchliche Beschriftungen brechen ab.
    """
    if not documents or len(documents) > 54:
        raise DetailImportError("Ungültige Anzahl von Planantworten.")
    references = {}
    block_count = 0
    for document in documents:
        try:
            soup = _page(document)
            blocks = soup.select(COURSE_BLOCK_SELECTOR)
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
                key = (identity_policy.key_for(client, target) if identity_policy
                       else hashlib.sha256(target.encode("utf-8")).hexdigest())
                previous = references.get(key)
                if previous is not None and previous.caption != caption:
                    raise DetailImportError("Dasselbe Detailziel hat widersprüchliche Beschriftungen.")
                references[key] = CourseReference(
                    key, target, caption,
                    previous.block_count + 1 if previous else 1,
                    "configured" if identity_policy else "run",
                )
        except (FormNavigationError, SourceFetchError, SourceIdentityError):
            raise DetailImportError("Planstruktur oder Detailziel konnte nicht sicher zugeordnet werden.") from None
    return tuple(references.values())


def fetch_detail_sample(client: SourceClient, references: tuple[CourseReference, ...], *,
                        semester: str, study_key: str, regulations_key: str,
                        limit: int = 2) -> DetailSample:
    """Maximal zehn eindeutige Detailziele; bei Abruf-/Parserfehlern kein Teilergebnis."""
    validate_detail_context(semester, study_key, regulations_key, limit)
    if (not references or len({ref.location for ref in references}) != len(references) or
            len({(ref.identity_scope, ref.key) for ref in references}) != len(references)):
        raise DetailImportError("Ungültige oder doppelte Detailauswahl.")
    details = []
    for reference in references[:limit]:
        blocking_reason = None
        try:
            document = client.fetch(reference.location)
            course = parse_course_detail(document.html, expected_semester=semester)
        except (SourceFetchError, SourceParseError):
            raise DetailImportError("Detailstichprobe abgebrochen: Abruf, Semester oder Parserstruktur ungeklärt.") from None
        try:
            preview = normalize_course(course, CourseContext(
                reference.key, study_key, regulations_key, semester,
                source_key_verified=reference.identity_scope == "configured",
            ))
            status = "preview"
        except NormalizationError as error:
            blocking_reason = error.code
            # Ein korrekt gelesenes Detail kann noch nicht interpretierte Sonderfälle enthalten.
            preview, status = None, "normalization_requires_review"
        details.append(DetailResult(reference.key, len(course.series), status, preview,
                                    course if preview is None else None, blocking_reason, course))
    return DetailSample(len(references), sum(ref.block_count for ref in references), tuple(details))
