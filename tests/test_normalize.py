from dataclasses import replace
from datetime import date, time
import json

import pytest

from backend.parser.course import CourseDetail, ScheduleSeries
from backend.parser.normalize import CourseContext, NormalizationError, normalize_course
from backend.importer.coverage import WeekResult, check_week_coverage


@pytest.fixture
def course():
    return CourseDetail(None, "Fiktive Veranstaltung", None, "Labor", "DEMO-Semester",
                        (ScheduleSeries(0, time(8), time(9), date(2025, 10, 20), date(2025, 11, 3),
                                        "woch", "DEMO", None, None, None, None),),
                        ("missing_source_identifier",))


@pytest.fixture
def context():
    return CourseContext("DEMO-1", "DEMO-STUDIUM", "DEMO-PO", "DEMO-Semester")


def changed(course, **kwargs):
    return replace(course, series=(replace(course.series[0], **kwargs),))


def test_weekly_times_follow_dst_and_json_is_only_preview(course, context):
    preview = normalize_course(course, context)
    assert [event.starts_at for event in preview.occurrences] == [
        "2025-10-20T06:00:00+00:00", "2025-10-27T07:00:00+00:00", "2025-11-03T07:00:00+00:00",
    ]
    result = json.loads(preview.to_json())
    assert result["complete"] is False
    assert "missing_source_identifier" not in result["review_reasons"]
    assert "source_context_requires_verification" in result["review_reasons"]
    assert context.source_key not in preview.to_json()


def test_identity_survives_title_and_room_changes_but_separates_contexts(course, context):
    key = normalize_course(course, context).course_key
    assert normalize_course(replace(course, title="Anderer Titel"), context).course_key == key
    assert normalize_course(changed(course, room="Anderer Raum"), context).course_key == key
    for field in ("source_key", "study_key", "regulations_key"):
        assert normalize_course(course, replace(context, **{field: "DEMO-2"})).course_key != key


def test_invalid_identity_and_semester_rejected(course, context):
    for bad in (replace(context, source_key=""), replace(context, source_key="https://example.invalid"),
                replace(context, semester="Anderes Semester")):
        with pytest.raises(NormalizationError):
            normalize_course(course, bad)


def test_explicit_cancellations_remove_only_exact_dates(course, context):
    result = normalize_course(changed(course, cancellation_text="20.10.2025; 03.11.2025"), context)
    assert [event.local_date for event in result.occurrences] == ["2025-10-27"]
    assert "cancellations_require_review" in result.review_reasons


def test_later_invalid_series_never_returns_partial_result(course, context):
    course = replace(course, series=course.series + (replace(course.series[0], recurrence="unbekannt"),))
    with pytest.raises(NormalizationError):
        normalize_course(course, context)


def test_all_cancelled_is_empty_preview_not_import_confirmation(course, context):
    result = normalize_course(changed(course, cancellation_text="20.10.2025,27.10.2025,03.11.2025"), context)
    assert result.occurrences == ()
    assert not result.complete


@pytest.mark.parametrize("text", ["Ferien", "20.10.", "31.02.2025", "21.10.2025", "06.10.2025",
                                   "20.10.2025; siehe Hinweis"])
def test_unclear_or_inconsistent_cancellation_rejects_whole_course(course, context, text):
    with pytest.raises(NormalizationError):
        normalize_course(changed(course, cancellation_text=text), context)


@pytest.mark.parametrize("kwargs", [{"recurrence": "unbekannt"}, {"note": "Gruppe A"},
                                   {"execution_note": "Nach Absprache"}])
def test_unverified_semantics_are_never_guessed(course, context, kwargs):
    with pytest.raises(NormalizationError):
        normalize_course(changed(course, **kwargs), context)


def test_single_and_block_require_explicit_rules(course, context):
    single = changed(course, recurrence="DEMO-EINZEL", valid_until=date(2025, 10, 20))
    with pytest.raises(NormalizationError):
        normalize_course(single, context)
    assert len(normalize_course(single, context, recurrence_rules={"DEMO-EINZEL": "single"}).occurrences) == 1
    block = changed(course, recurrence="DEMO-BLOCK", valid_until=date(2025, 10, 22))
    assert len(normalize_course(block, context, recurrence_rules={"DEMO-BLOCK": "daily"}).occurrences) == 3
    with pytest.raises(NormalizationError):
        normalize_course(block, context, recurrence_rules={"DEMO-BLOCK": "single"})


@pytest.mark.parametrize("day", [date(2025, 3, 30), date(2025, 10, 26)])
def test_nonexistent_or_ambiguous_clock_rejected(course, context, day):
    with pytest.raises(NormalizationError):
        normalize_course(changed(course, weekday=6, valid_from=day, valid_until=day,
                                 start_time=time(2, 30), end_time=time(3, 30)), context)


def test_iso_year_differs_from_calendar_year(course, context):
    result = normalize_course(changed(course, valid_from=date(2025, 12, 29),
                                     valid_until=date(2025, 12, 29)), context)
    assert (result.occurrences[0].iso_year, result.occurrences[0].iso_week) == (2026, 1)


def test_coverage_includes_partial_boundary_weeks_and_confirmed_empty():
    result = check_week_coverage(date(2025, 12, 28), date(2026, 1, 5), [
        WeekResult(2025, 52, "ok"), WeekResult(2026, 1, "empty_confirmed"), WeekResult(2026, 2, "ok"),
    ])
    assert result.weeks_complete


def test_coverage_missing_failed_unexpected_and_duplicate_do_not_pass():
    result = check_week_coverage(date(2025, 12, 28), date(2026, 1, 5), [
        WeekResult(2025, 52, "ok"), WeekResult(2025, 52, "ok"),
        WeekResult(2026, 1, "login"), WeekResult(2026, 3, "ok"),
    ])
    assert result.missing == ((2026, 2),)
    assert result.failed == ((2026, 1),)
    assert result.duplicates == ((2025, 52),)
    assert result.unexpected == ((2026, 3),)
    assert not result.weeks_complete


def test_empty_response_is_not_confirmed_empty_week():
    assert not check_week_coverage(date(2026, 1, 1), date(2026, 1, 1), []).weeks_complete
    assert not check_week_coverage(date(2026, 1, 1), date(2026, 1, 1),
                                   [WeekResult(2026, 1, "empty")]).weeks_complete


def test_invalid_week_and_reversed_interval():
    with pytest.raises(ValueError):
        check_week_coverage(date(2026, 1, 1), date(2026, 1, 1), [WeekResult(2026, 54, "ok")])
    with pytest.raises(ValueError):
        check_week_coverage(date(2026, 2, 1), date(2026, 1, 1), [])

@pytest.mark.parametrize("note,kind", [("Vorlesung", "teaching_format"), ("Labor X9.8.76", "room_hint")])
def test_verified_series_labels_preserve_text_without_altering_events(course, context, note, kind):
    original = normalize_course(course, context)
    preview = normalize_course(changed(course, note=note), context)
    assert preview.occurrences == original.occurrences
    assert preview.series_annotations[0].text == note
    assert preview.series_annotations[0].kind == kind
    assert preview.series_annotations[0].series_index == 0
    assert "notes_require_review" in preview.review_reasons
    assert not preview.complete
    if kind == "room_hint":
        assert "room_note_requires_review" in preview.review_reasons
        assert all(event.room == "DEMO" for event in preview.occurrences)
    assert json.loads(preview.to_json())["series_annotations"][0]["text"] == note


def test_makeup_label_only_annotates_explicit_single(course, context):
    single = changed(course, recurrence="Einzel", valid_until=date(2025, 10, 20))
    original = normalize_course(single, context)
    preview = normalize_course(changed(single, note="Nachholtermin"), context)
    assert preview.occurrences == original.occurrences
    assert preview.series_annotations[0].kind == "makeup_label"
    assert "replacement_reference_requires_review" in preview.review_reasons
    assert "replacement_id" not in preview.to_json()
    assert not preview.complete


@pytest.mark.parametrize("note", ["Nachholtermin", "Vorlesung nur jede zweite Woche", "Vorlesung entfällt",
                                  "Labor X9.8.76 ab 12 Uhr", "Gruppe A", "Vorlesung<script>"])
def test_unknown_or_temporal_note_is_not_silently_accepted(course, context, note):
    with pytest.raises(NormalizationError):
        normalize_course(changed(course, note=note), context)


def test_annotation_series_indices_and_late_failure_are_atomic(course, context):
    series = (replace(course.series[0], note="Vorlesung"), replace(course.series[0], note="Labor X9.8.76"))
    preview = normalize_course(replace(course, series=series), context)
    assert [a.series_index for a in preview.series_annotations] == [0, 1]
    with pytest.raises(NormalizationError):
        normalize_course(replace(course, series=series + (replace(course.series[0], note="Unbekannte Regel"),)), context)