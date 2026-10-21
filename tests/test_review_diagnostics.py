"""Fiktive Importfälle: Ursachen sichtbar halten, ohne Quelldaten auszugeben."""
from dataclasses import replace
from pathlib import Path
import json

import pytest

from backend.importer.details import DetailResult, DetailSample, fetch_detail_sample, CourseReference
from backend.importer.http import SourceClient, SourceDocument
from backend.importer.semester import completeness_review, SemesterViewResult
from backend.parser import parse_course_detail, normalize_course, CourseContext, NormalizationError


def course():
    return parse_course_detail((Path(__file__).parent / 'fixtures/course_detail.html').read_text())


@pytest.mark.parametrize('changes,code', [
    ({'note': 'PRIVATE https://example.invalid/private'}, 'unsupported_series_note'),
    ({'recurrence': 'PRIVATE'}, 'unsupported_recurrence'),
    ({'execution_note': 'PRIVATE'}, 'unsupported_execution_note'),
    ({'cancellation_text': 'PRIVATE'}, 'unsupported_cancellation_format'),
    ({'cancellation_text': '01.01.2000'}, 'cancellation_outside_series'),
])
def test_blockers_have_fixed_codes_and_no_source_text(changes, code):
    source = course()
    source = replace(source, series=(replace(source.series[0], **changes),))
    with pytest.raises(NormalizationError) as error:
        normalize_course(source, CourseContext('DEMO', 'DEMO', 'PO', source.semester))
    assert error.value.code == code
    assert 'PRIVATE' not in str(error.value)


def test_fetch_keeps_blocking_cause_and_summary_sanitized(monkeypatch):
    html = (Path(__file__).parent / 'fixtures/course_detail.html').read_text()
    source = course()
    source = replace(source, series=(replace(source.series[0], note='PRIVATE'),))
    monkeypatch.setattr('backend.importer.details.parse_course_detail', lambda *a, **kw: source)
    with SourceClient('https://example.invalid/start') as client:
        monkeypatch.setattr(client, 'fetch', lambda url: SourceDocument(html, url))
        sample = fetch_detail_sample(client, (CourseReference('secret-key', 'https://example.invalid/detail', 'PRIVATE', 1),),
                                     semester=source.semester, study_key='DEMO', regulations_key='PO')
    summary = sample.review_summary()
    assert summary['reason_counts'] == {'unsupported_series_note': 1}
    assert summary['details'] == [{'detail_number': 1, 'blocked': True, 'reasons': ['unsupported_series_note']}]
    assert sample.details[0].unresolved_course is source
    assert not any(word in json.dumps(summary) for word in ('PRIVATE', 'secret-key', 'example.invalid'))


def test_valid_normalization_never_proves_semester_coverage():
    source = course()
    preview = normalize_course(source, CourseContext('DEMO', 'DEMO', 'PO', source.semester, True))
    detail = DetailResult('DEMO', len(source.series), 'preview', preview)
    sample = DetailSample(1, 1, (detail,))
    views = tuple(SemesterViewResult(name, 'observed', 1, 0, ()) for name in ('semester', 'special_dates'))
    review = completeness_review(views, sample)
    assert not review['eligible_for_publication']
    assert 'semester_extent_unverified' in review['blockers']
    assert 'weekend_coverage_unverified' in review['blockers']
    assert 'details_unchecked' not in review['blockers']
    assert 'normalization_blocked' not in review['blockers']
    summary = sample.review_summary()
    assert summary['reason_counts']['study_context_requires_verification'] == 1


def test_missing_views_unchecked_and_blocked_details_stay_visible():
    sample = DetailSample(2, 2, (DetailResult('DEMO', 1, 'normalization_requires_review', None),))
    views = (SemesterViewResult('semester', 'empty_unverified', 0, 0, ()),)
    blockers = completeness_review(views, sample)['blockers']
    assert {'semester_views_missing', 'semester_view_empty_or_unverified',
            'details_unchecked', 'normalization_blocked'} <= set(blockers)
    assert sample.review_summary()['reason_counts'] == {'normalization_requires_review': 1}


@pytest.mark.parametrize("scope,unverified", [("run", True), ("configured", False)])
def test_completeness_does_not_hide_unverified_source_identity(scope, unverified):
    reference = CourseReference("DEMO", "https://example.invalid/detail", "Fiktiver Kurs", 1, scope)
    views = tuple(SemesterViewResult(name, "observed", 1, 0, (reference,))
                  for name in ("semester", "special_dates"))
    result = completeness_review(views)
    assert ("source_identity_unverified" in result["blockers"]) is unverified
    assert not result["eligible_for_publication"]
    assert "details_unchecked" in result["blockers"]
