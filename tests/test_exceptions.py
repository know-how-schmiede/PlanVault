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
    "27.10.2025: Verlegt auf 29.10.2025",
    "27.10.2025: Verlegt auf 29.10.",
    "27.10.2025:",
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
