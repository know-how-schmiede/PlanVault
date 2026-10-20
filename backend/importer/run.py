"""Gemeinsamer, unveröffentlichter Import-Prüflauf mit bereinigtem Bericht."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import json
from uuid import uuid4

from backend.importer.coverage import check_week_coverage
from backend.importer.details import (
    DetailImportError, collect_course_references, fetch_detail_sample,
    merge_course_references, validate_detail_context,
)
from backend.importer.forms import FormNavigationError
from backend.importer.http import SourceClient, SourceFetchError
from backend.importer.navigation import search_study, follow_named_result, submit_labeled_search
from backend.importer.weeks import audit_weeks
from backend.importer.identity import SourceIdentityPolicy
from version import __version__


class ImportCheckInputError(ValueError):
    """Ungültiger Prüfauftrag, ohne Rückgabe vertraulicher Eingabewerte."""


@dataclass(frozen=True)
class ImportCheckReport:
    schema_version: int
    run_id: str
    app_version: str
    started_at: str
    finished_at: str
    status: str
    stage: str
    period_start: str
    period_end: str
    requested_weeks: tuple[tuple[int, int], ...]
    checked_weeks: tuple[tuple[int, int, str], ...]
    missing_weeks: tuple[tuple[int, int], ...]
    failed_weeks: tuple[tuple[int, int], ...]
    reference_count: int
    checked_details: int
    unchecked_details: int
    normalization_review_count: int
    blockers: tuple[str, ...]
    identity_mode: str
    complete: bool = False
    published: bool = False

    def to_json(self) -> str:
        # Nur dieses explizite Berichtsmodell serialisieren, niemals Quellobjekte.
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, indent=2)


def run_import_check(client: SourceClient, *, query: str, title: str, semester: str,
                     study_key: str, regulations_key: str, start: date, end: date,
                     requested: tuple[tuple[int, int], ...], detail_limit: int = 2,
                     identity_policy: SourceIdentityPolicy | None = None) -> ImportCheckReport:
    """Navigation → Wochenprüfung → gemeinsame Detailstichprobe; kein Archivschreiben.

    Erwartete Quellfehler ergeben einen fehlgeschlagenen Bericht. Programmierfehler
    werden nicht pauschal abgefangen. Eingabefehler werden vor Netzwerkzugriff abgelehnt.
    """
    validate_detail_context(semester, study_key, regulations_key, detail_limit)
    try:
        coverage = check_week_coverage(start, end, [])
    except ValueError:
        raise ImportCheckInputError("Ungültiger Prüfzeitraum.") from None
    if (not query.strip() or len(query) > 200 or not title.strip() or not requested or
            len(requested) > 54 or len(set(requested)) != len(requested)):
        raise ImportCheckInputError("Ungültige Auswahl für den Import-Prüflauf.")
    for key in requested:
        try:
            date.fromisocalendar(*key, 1)
        except (ValueError, TypeError):
            raise ImportCheckInputError("Ungültige ISO-Woche.") from None
        if key not in coverage.missing:
            raise ImportCheckInputError("Angeforderte Woche liegt außerhalb des Prüfzeitraums.")
    run_id = str(uuid4())
    started = datetime.now(timezone.utc).isoformat()
    stage, status = "navigation", "needs_review"
    checked_weeks = ()
    references = ()
    sample = None
    blockers = {"semester_content_unverified",
                "study_context_unverified" if identity_policy else "source_identity_unverified"}
    try:
        results = search_study(client, query)
        selection = follow_named_result(client, results, title=title)
        plan = submit_labeled_search(client, selection, field_label="Studiengang", button_caption="Suche starten")
        stage = "weeks"

        def collect(document):
            nonlocal references
            references = merge_course_references((references, collect_course_references(
                client, (document,), identity_policy=identity_policy,
            )))

        audit = audit_weeks(client, plan, start=start, end=end, requested=requested, on_week=collect)
        coverage = audit.coverage
        checked_weeks = tuple((result.iso_year, result.iso_week, result.status) for result in audit.results)
        if coverage.failed or coverage.unexpected or coverage.duplicates:
            blockers.add("weeks_require_review")
            if any(result.status == "failed" for result in audit.results):
                status = "failed"
        else:
            stage = "details"
            sample = fetch_detail_sample(client, references, semester=semester, study_key=study_key,
                                         regulations_key=regulations_key, limit=detail_limit)
            stage = "finished"
    except (SourceFetchError, FormNavigationError, DetailImportError):
        status = "failed"
        blockers.add(f"{stage}_failed")
    if coverage.missing:
        blockers.add("missing_weeks")
    checked = len(sample.details) if sample else 0
    unchecked = len(references) - checked
    if unchecked:
        blockers.add("unchecked_details")
    review_count = sum(detail.requires_review for detail in sample.details) if sample else 0
    if review_count:
        blockers.add("normalization_requires_review")
    return ImportCheckReport(
        2, run_id, __version__, started, datetime.now(timezone.utc).isoformat(), status, stage,
        start.isoformat(), end.isoformat(), requested, checked_weeks, coverage.missing, coverage.failed,
        len(references), checked, unchecked, review_count, tuple(sorted(blockers)),
        "configured" if identity_policy else "run",
    )
