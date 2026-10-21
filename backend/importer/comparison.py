"""Begrenzter Vergleich von Veranstaltungszielen, ohne Import oder Veröffentlichung."""

from datetime import date, datetime, timezone
from uuid import uuid4

from backend.importer.coverage import check_week_coverage
from backend.importer.details import collect_course_references, merge_course_references, DetailImportError
from backend.importer.forms import FormNavigationError
from backend.importer.http import SourceFetchError
from backend.importer.identity import SourceIdentityPolicy
from backend.importer.navigation import search_study, follow_named_result, submit_labeled_search, _page
from backend.importer.semester import audit_semester_views, validate_semester_details
from backend.importer.structure import COURSE_BLOCK_SELECTOR
from backend.importer.weeks import read_week_menu, audit_weeks
from backend.importer.presence import fetch_comparison_details, compare_weekly_presence
from version import __version__


class ComparisonInputError(ValueError):
    """Ungültiger Auftrag; ausschließlich bereinigte Meldungen."""


def validate_comparison(query, title, start, end, requested, week_budget, identity_policy):
    if not isinstance(identity_policy, SourceIdentityPolicy):
        raise ComparisonInputError("Ansichtsabgleich benötigt eine konfigurierte Quellkennung.")
    if (not isinstance(query, str) or not query.strip() or len(query) > 200 or
            not isinstance(title, str) or not title.strip() or len(title) > 200):
        raise ComparisonInputError("Ungültige Studiengangsauswahl.")
    if (type(start) is not date or type(end) is not date or
            not isinstance(week_budget, int) or isinstance(week_budget, bool) or
            not 1 <= week_budget <= 54):
        raise ComparisonInputError("Ungültiger Prüfzeitraum oder Wochenbudget.")
    try:
        expected = check_week_coverage(start, end, []).missing
    except ValueError:
        raise ComparisonInputError("Ungültiger Prüfzeitraum.") from None
    selection = expected if requested is None else requested
    if (not isinstance(selection, tuple) or not selection or len(selection) > week_budget or
            any(not isinstance(key, tuple) or len(key) != 2 or
                any(type(number) is not int for number in key) for key in selection)):
        raise ComparisonInputError("Wochenauftrag ist leer, ungültig oder überschreitet das Budget.")
    if len(set(selection)) != len(selection) or any(key not in expected for key in selection):
        raise ComparisonInputError("Doppelte Wochen oder Wochen außerhalb des Prüfzeitraums.")
    return expected, selection


def compare_references(semester_references, week_references):
    """Nur laufbezogene Nummern ausgeben; keine Quellkennungen oder Beschriftungen."""
    merged = merge_course_references((semester_references, week_references))
    if any(r.identity_scope != "configured" for r in merged):
        raise DetailImportError("Ansichtsabgleich benötigt konfigurierte Veranstaltungskennungen.")
    numbers = {r.key: index for index, r in enumerate(merged, 1)}
    semester = {r.key for r in semester_references}
    weeks = {r.key for r in week_references}
    return {
        "semester_reference_count": len(semester), "week_reference_count": len(weeks),
        "shared_reference_count": len(semester & weeks),
        "only_in_weeks": sorted(numbers[key] for key in weeks - semester),
        "only_in_semester_views": sorted(numbers[key] for key in semester - weeks),
        "reference_sets_equal": semester == weeks,
    }


def run_view_comparison(client, *, query, title, start, end, identity_policy,
                        requested=None, week_budget=30, details=False, semester=None,
                        study_key=None, regulations_key=None, detail_budget=80,
                        on_observed_week=None, on_details=None):
    """Alle erwarteten oder ausgewählte Wochen mit beiden Semesteransichten vergleichen.

    Zeitraum und Budget kommen vom Aufrufer, nicht aus dem Quellmenü. Tageshinweise
    bleiben prüfpflichtig; strukturgeprüfte Seiten können dennoch Ziele beitragen.
    Mit details zusätzlich bekannte Detailziele einmalig lesen und Wochenpräsenz
    vergleichen. Abruf-/Strukturfehler liefern keinen erfolgreichen Teilvergleich.
    """
    expected, selection = validate_comparison(query, title, start, end, requested,
                                               week_budget, identity_policy)
    if details:
        validate_semester_details(semester, study_key, regulations_key, detail_budget)
    started = datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": 4, "app_version": __version__, "run_id": str(uuid4()),
        "started_at": started, "status": "needs_review", "stage": "navigation",
        "period_start": start.isoformat(), "period_end": end.isoformat(),
        "identity_mode": "configured", "requested_weeks": selection,
        "unavailable_weeks": [], "checked_weeks": [], "missing_weeks": expected,
        "review_weeks": [], "failed_weeks": [], "views": [], "unresolved_day_notices": [],
        "all_requested_weeks_observed": False, "period_weeks_verified": False,
        "comparison_evaluated": False, "comparison_scope": "observed_weeks", "comparison": None,
        "details_requested": details, "checked_details": 0,
        "normalization_summary": None, "review_summary": None, "weekly_presence": None,
        "weekend_coverage_verified": False, "complete": False, "published": False,
    }
    blockers = {"semester_extent_unverified", "study_context_unverified",
                "weekend_coverage_unverified", "detail_content_unchecked"}
    try:
        results = search_study(client, query)
        selected = follow_named_result(client, results, title=title)
        plan = submit_labeled_search(client, selected, field_label="Studiengang",
                                     button_caption="Suche starten")
        menu = read_week_menu(plan)
        available = {choice.key for choice in menu.choices}
        report["unavailable_weeks"] = sorted(set(selection) - available)
        if report["unavailable_weeks"]:
            blockers.add("requested_weeks_unavailable")
        report["stage"] = "semester_views"
        views = audit_semester_views(client, plan, identity_policy=identity_policy)
        report["views"] = [{"view": v.view, "status": v.status,
                            "reference_count": v.reference_count} for v in views]
        if any(v.status != "observed" for v in views):
            blockers.add("semester_view_empty_or_unverified")
        semester_refs = merge_course_references(tuple(v.references for v in views))
        week_refs = ()
        observed = []
        week_targets = {}
        week_statuses = {}
        day_notices = {}

        def collect(document, result):
            nonlocal week_refs
            if on_observed_week is not None:
                on_observed_week(document, result)
            try:
                refs = (collect_course_references(client, (document,), identity_policy=identity_policy)
                        if _page(document).select(COURSE_BLOCK_SELECTOR) else ())
                week_refs = merge_course_references((week_refs, refs))
            except DetailImportError:
                raise FormNavigationError("Veranstaltungsziele der Woche benötigen Prüfung.") from None
            week = (result.iso_year, result.iso_week)
            week_targets[week] = {r.key for r in refs}
            week_statuses[week] = result.status
            day_notices[week] = result.day_notices
            observed.append({"iso_year": result.iso_year, "iso_week": result.iso_week,
                             "status": result.status, "reference_count": len(refs)})

        report["stage"] = "weeks"
        offered_selection = tuple(key for key in selection if key in available)
        audit = (audit_weeks(client, plan, start=start, end=end, requested=offered_selection,
                             on_observed_week=collect, continue_on_review=True)
                 if offered_selection else None)
        results = audit.results if audit else ()
        report["checked_weeks"] = [
            {"iso_year": r.iso_year, "iso_week": r.iso_week, "status": r.status,
             "day_notices": [{"local_date": n.local_date, "kind": n.kind} for n in r.day_notices],
             "reference_count": next((w["reference_count"] for w in observed
                                      if (w["iso_year"], w["iso_week"]) == (r.iso_year, r.iso_week)), None)}
            for r in results
        ]
        report["unresolved_day_notices"] = [
            {"local_date": notice.local_date, "kind": notice.kind}
            for result in results for notice in result.day_notices
            if notice.kind in {"unnamed", "unclassified"}
        ]
        if any(n["kind"] == "unnamed" for n in report["unresolved_day_notices"]):
            blockers.add("unnamed_day_notices_require_review")
        if any(n["kind"] == "unclassified" for n in report["unresolved_day_notices"]):
            blockers.add("unclassified_day_notices_require_review")
        coverage = check_week_coverage(start, end, results)
        report["missing_weeks"] = coverage.missing
        report["review_weeks"] = [(r.iso_year, r.iso_week) for r in results
                                  if r.status not in {"ok", "failed"}]
        report["failed_weeks"] = [(r.iso_year, r.iso_week) for r in results if r.status == "failed"]
        report["all_requested_weeks_observed"] = set(selection) <= {
            (r.iso_year, r.iso_week) for r in results if r.status != "failed"}
        report["period_weeks_verified"] = coverage.weeks_complete
        if report["review_weeks"]:
            blockers.add("weeks_require_review")
        if report["failed_weeks"]:
            raise FormNavigationError("Wochenprüfung abgebrochen.")
        report["stage"] = "comparison"
        if observed:
            report["comparison"] = compare_references(semester_refs, week_refs)
            report["comparison_evaluated"] = True
            if report["comparison"]["only_in_weeks"]:
                blockers.add("references_missing_from_semester_views")
            if report["comparison"]["only_in_semester_views"]:
                blockers.add("semester_references_not_observed_in_weeks")
        else:
            blockers.add("no_week_inventory")
        if details and observed:
            report["stage"] = "details"
            references = merge_course_references((semester_refs, week_refs))
            sample = fetch_comparison_details(client, references, semester=semester,
                                               study_key=study_key, regulations_key=regulations_key,
                                               budget=detail_budget)
            if on_details is not None:
                on_details(references, sample)
            report["stage"] = "weekly_presence"
            presence = compare_weekly_presence(references, sample, week_targets, week_statuses,
                                               start=start, end=end, day_notices=day_notices)
            report["checked_details"] = len(sample.details)
            report["normalization_summary"] = sample.normalization_summary()
            report["review_summary"] = sample.review_summary()
            report["weekly_presence"] = presence
            blockers.discard("detail_content_unchecked")
            blockers.add("occurrence_fields_unverified")
            if presence["blocked_details"]:
                blockers.add("normalization_blocked")
            if presence["review_details"]:
                blockers.add("detail_review_required")
            if presence["missing_from_week_view"] or presence["observed_without_expected_occurrence"]:
                blockers.add("weekly_presence_mismatch")
            if not presence["evaluated"]:
                blockers.add("weekly_presence_not_evaluated")
            if presence["partial_boundary_weeks"]:
                blockers.add("partial_boundary_weeks_not_compared")
        report["stage"] = "finished"
    except (SourceFetchError, FormNavigationError, DetailImportError):
        report["status"] = "failed"
        blockers.add(report["stage"] + "_failed")
        report["comparison_evaluated"] = False
        report["comparison"] = None
        report["checked_details"] = 0
        report["normalization_summary"] = None
        report["review_summary"] = None
        report["weekly_presence"] = None
    if report["missing_weeks"]:
        blockers.add("missing_weeks")
    report["blockers"] = sorted(blockers)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    return report
