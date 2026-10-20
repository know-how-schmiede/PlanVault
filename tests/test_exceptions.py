from pathlib import Path
import json

import pytest

from backend.parser import CourseContext, NormalizationError, parse_course_detail, normalize_course
from backend.importer.details import DetailResult


@pytest.fixture
def html():
    return (Path(__file__).parent / "fixtures/course_exceptions.html").read_text(encoding="utf-8")


def normalize(html):
    course = parse_course_detail(html, expected_semester="WiSe 2025/26")
    return normalize_course(course, CourseContext("DEMO", "DEMO-STUDY", "DEMO-PO", course.semester))


def test_verified_single_and_annotated_cancellation_preserved_separately(html):
    course = parse_course_detail(html)
    assert "unverified_recurrence" not in course.review_reasons
    result = normalize(html)
    assert [event.local_date for event in result.occurrences] == ["2025-10-20", "2025-10-29", "2025-11-03"]
    assert len(result.cancellations) == 1
    cancellation = result.cancellations[0]
    assert cancellation.local_date == "2025-10-27"
    assert cancellation.series_index == 0
    assert cancellation.note == "Fiktiver Ausfall für den Test"
    assert "special_recurrence_requires_verification" not in result.review_reasons
    assert "cancellations_require_review" in result.review_reasons
    assert not result.complete
    # Kein automatisch behaupteter Zusammenhang zwischen Ausfall und Einzeltermin.
    assert "replacement" not in result.to_json()


def test_preview_json_retains_cancellation_reason(html):
    result = json.loads(normalize(html).to_json())
    assert result["cancellations"] == [{
        "local_date": "2025-10-27", "note": "Fiktiver Ausfall für den Test", "series_index": 0,
    }]


@pytest.mark.parametrize("replacement", [
    "31.02.2025: Fiktiver Ausfall",
    "28.10.2025: Fiktiver Ausfall",
    "27.10.2025: " + "x" * 501,
])
def test_unverified_annotated_cancellation_rejected(html, replacement):
    with pytest.raises(NormalizationError):
        normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test", replacement))


def test_single_with_multiple_dates_is_not_expanded(html):
    with pytest.raises(NormalizationError):
        normalize(html.replace("29.10.2025 - 29.10.2025", "29.10.2025 - 05.11.2025"))


def test_recognized_preview_with_cancellations_still_requires_review(html):
    preview = normalize(html)
    result = DetailResult("DEMO", 2, "preview", preview)
    assert result.requires_review


def test_no_cancellation_means_single_requires_no_extra_rhythm_review(html):
    result = normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test", ""))
    assert result.cancellations == ()
    assert result.review_reasons == ("source_context_requires_verification",)
    assert not DetailResult("DEMO", 2, "preview", result).requires_review

@pytest.mark.parametrize("value,notes", [
    ("20.10.2025: 27.10.2025:", [None, None]),
    ("20.10.2025: Fiktiver Raum A1.3.05 27.10.2025: Fiktiver Hinweis", ["Fiktiver Raum A1.3.05", "Fiktiver Hinweis"]),
    ("27.10.2025:", [None]),
])
def test_multiple_and_empty_annotated_cancellations(html, value, notes):
    result = normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test", value))
    assert [c.note for c in result.cancellations] == notes
    assert "cancellations_require_review" in result.review_reasons
    assert not result.complete
    assert not any(o.local_date in {c.local_date for c in result.cancellations} for o in result.occurrences)


@pytest.mark.parametrize("value", [
    "27.10.2025: 27.10.2025: Fiktiver Konflikt",
    "20.10.2025: 28.10.2025:",
    "20.10.2025: 31.02.2025:",
])
def test_multiple_cancellations_reject_ambiguity_atomically(html, value):
    with pytest.raises(NormalizationError):
        normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test", value))


def test_summary_distinguishes_blocked_and_review_previews(html):
    from backend.importer.details import DetailSample
    preview = normalize(html)
    sample = DetailSample(2, 2, (DetailResult("DEMO", 2, "preview", preview),
                                DetailResult("OTHER", 1, "normalization_requires_review", None)))
    assert sample.normalization_summary() == {
        "preview_count": 1, "blocked_count": 1, "review_preview_count": 1,
    }
@pytest.mark.parametrize("note", ["Verlegt auf 29.10.2025", "Verlegt auf 29.10.",
                                  "Verlegt auf 29/10, 15:30-18:45", "Verlegt auf 31.02.2025"])
def test_replacement_text_is_preserved_without_creating_or_linking_events(html, note):
    result = normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test", "27.10.2025: " + note))
    assert result.cancellations[0].note == note
    assert [o.local_date for o in result.occurrences] == ["2025-10-20", "2025-10-29", "2025-11-03"]
    assert "replacement_reference_requires_review" in result.review_reasons
    assert not result.complete
    assert DetailResult("DEMO", 2, "preview", result).requires_review
    assert "replacement_id" not in result.to_json()


def test_replacement_text_does_not_change_the_independent_single_event(html):
    result = normalize(html.replace("27.10.2025: Fiktiver Ausfall für den Test",
                                    "27.10.2025: Verlegt auf 29.10., 15:30-18:45"))
    original = normalize(html)
    assert result.occurrences == original.occurrences