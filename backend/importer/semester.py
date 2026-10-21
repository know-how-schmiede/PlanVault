"""Begrenzte Bestandsaufnahme zusätzlicher Semesteransichten."""

from dataclasses import dataclass, field
from datetime import date

from backend.importer.structure import COURSE_BLOCK_SELECTOR
from backend.importer.details import (
    collect_course_references, CourseReference, merge_course_references,
    fetch_detail_sample, validate_detail_context, DetailImportError, DetailSample,
)
from backend.importer.forms import FormNavigationError
from backend.importer.identity import SourceIdentityPolicy
from backend.importer.navigation import _page, _caption
from backend.importer.weeks import read_week_menu


VIEWS = (
    ("semester", "Semesteransicht"),
    ("special_dates", "Semesterzeitansicht nur Block/Einzeltermine"),
)


def weekday_coverage(views, sample=None):
    """Beobachtete Tage zählen, ohne aus fehlenden Terminen Leerbestand abzuleiten."""
    visible = set().union(*(set(v.visible_weekdays) for v in views))
    counts = [0] * 7
    if sample is not None:
        for detail in sample.details:
            if detail.preview is not None:
                for event in detail.preview.occurrences:
                    counts[date.fromisoformat(event.local_date).weekday()] += 1
    return {
        "visible_weekdays": sorted(visible),
        "unobserved_weekdays": sorted(set(range(7)) - visible),
        "occurrences_by_weekday": counts,
        "occurrence_weekdays_outside_views": [day for day in range(7) if counts[day] and day not in visible],
        "details_checked": sample is not None and sample.unchecked_count == 0,
        "blocked_details": None if sample is None else sum(d.preview is None for d in sample.details),
        "weekend_coverage_verified": False,
    }


def validate_semester_details(semester, study_key, regulations_key, budget):
    validate_detail_context(semester, study_key, regulations_key, 1)
    if not isinstance(budget, int) or isinstance(budget, bool) or not 1 <= budget <= 100:
        raise DetailImportError("Detailbudget muss zwischen eins und hundert liegen.")


def fetch_semester_details(client, views, *, semester, study_key, regulations_key, budget):
    """Alle bekannten Ziele oder Abbruch; kein stilles Abschneiden auf das Budget."""
    validate_semester_details(semester, study_key, regulations_key, budget)
    if (tuple(v.view for v in views) != tuple(code for code, _ in VIEWS) or
            any(v.status not in {"observed", "empty_unverified"} for v in views)):
        raise DetailImportError("Unvollständige Bestandsaufnahme der Semesteransichten.")
    references = merge_course_references(tuple(v.references for v in views))
    if not references or len(references) > budget:
        raise DetailImportError("Keine Detailziele oder Detailbudget überschritten.")
    if any(r.identity_scope != "configured" for r in references):
        raise DetailImportError("Semesterdetails benötigen konfigurierte Quellkennungen.")
    details = []
    for reference in references:
        sample = fetch_detail_sample(client, (reference,), semester=semester,
                                     study_key=study_key, regulations_key=regulations_key, limit=1)
        details.extend(sample.details)
    return DetailSample(len(references), sum(r.block_count for r in references), tuple(details))


@dataclass(frozen=True)
class SemesterViewResult:
    view: str
    status: str
    reference_count: int
    additional_count: int
    references: tuple[CourseReference, ...] = field(repr=False)
    visible_weekdays: tuple[int, ...] = ()


def audit_semester_views(client, document, *, identity_policy: SourceIdentityPolicy):
    """Zwei Ansichten sequenziell prüfen; keine Detailabrufe oder Freigabe.

    Leere Ansichten gelten nicht als bestätigter Leerbestand. Die zweite Ansicht
    wird gegen die erste verglichen, damit zusätzliche Ziele sichtbar bleiben.
    """
    if not isinstance(identity_policy, SourceIdentityPolicy):
        raise FormNavigationError("Semesterprüfung benötigt eine konfigurierte Quellkennung.")
    initial = read_week_menu(document)
    expected_weeks = tuple(c.key for c in initial.choices)
    results = []
    known = set()
    for code, label in VIEWS:
        menu = read_week_menu(document)
        soup = _page(document)
        selects = soup.find_all("select", attrs={"name": menu.field_name})
        if len(selects) != 1:
            raise FormNavigationError("Ansichtsauswahl ist mehrdeutig.")
        options = selects[0].find_all("option")
        matches = [o for o in options if _caption(o) == label]
        if (len(matches) != 1 or not matches[0].get("value") or
                matches[0].has_attr("disabled") or
                sum(o.get("value") == matches[0].get("value") for o in options) != 1):
            raise FormNavigationError("Semesteransicht fehlt oder ist mehrdeutig.")
        document = menu.form.submit(client, values={menu.field_name: (matches[0]["value"],)},
                                    button=menu.button)
        returned = read_week_menu(document)
        if tuple(c.key for c in returned.choices) != expected_weeks:
            raise FormNavigationError("Wochenangebot hat sich während der Semesterprüfung geändert.")
        soup = _page(document)
        selects = soup.find_all("select", attrs={"name": returned.field_name})
        selected = selects[0].find_all("option", selected=True) if len(selects) == 1 else []
        if len(selected) != 1 or _caption(selected[0]) != label:
            raise FormNavigationError("Quelle hat die angeforderte Semesteransicht nicht übernommen.")
        refs = (collect_course_references(client, (document,), identity_policy=identity_policy)
                if soup.select(COURSE_BLOCK_SELECTOR) else ())
        day_names = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
        visible_days = tuple(sorted({day_names.index(_caption(h)) for h in soup.find_all("th")
                                     if _caption(h) in day_names}))
        keys = {r.key for r in refs}
        results.append(SemesterViewResult(code, "observed" if refs else "empty_unverified",
                                         len(refs), len(keys - known) if results else 0, refs, visible_days))
        known.update(keys)
    return tuple(results)


def completeness_review(views, sample=None):
    """Offene Nachweise explizit ausweisen, ohne Freigabe abzuleiten."""
    blockers = {"study_context_unverified", "semester_extent_unverified",
                "weekend_coverage_unverified"}
    if tuple(v.view for v in views) != tuple(code for code, _ in VIEWS):
        blockers.add("semester_views_missing")
    if any(v.status != "observed" for v in views):
        blockers.add("semester_view_empty_or_unverified")
    if sample is None or sample.unchecked_count:
        blockers.add("details_unchecked")
    if sample is not None:
        if any(d.preview is None for d in sample.details):
            blockers.add("normalization_blocked")
        if any(d.preview is not None and d.requires_review for d in sample.details):
            blockers.add("detail_review_required")
    return {"blockers": sorted(blockers), "eligible_for_publication": False}
