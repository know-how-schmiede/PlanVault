"""Fiktive Prüfungen der Wochenpräsenz; keine Uhrzeit-/Raumfreigabe."""
from dataclasses import replace
from datetime import date, time, timedelta
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from backend import create_app
from backend.importer.comparison import run_view_comparison
from backend.importer.details import CourseReference, DetailResult, DetailSample, DetailImportError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.presence import compare_weekly_presence, fetch_comparison_details
from backend.parser.course import CourseDetail, ScheduleSeries
from backend.parser.normalize import CourseContext, normalize_course
from tests.test_view_comparison import workflow, START, END, POLICY

W0, W1 = (2026, 53), (2027, 1)


def detail(key, days, *, cancelled=(), note=None, clock=time(8)):
    series = tuple(ScheduleSeries(d.weekday(), clock, time(9), d, d, 'Einzel', 'DEMO-RAUM',
                                 'DEMO-LEHRPERSON', None, note,
                                 d.strftime('%d.%m.%Y') if d in cancelled else None) for d in days)
    course = CourseDetail(None, 'FIKTIVER TITEL', None, 'Demo', 'DEMO-Semester', series, ())
    preview = normalize_course(course, CourseContext(key, 'STUDY', 'PO', course.semester, True))
    return DetailResult(key, len(series), 'preview', preview)


def references(details):
    return tuple(CourseReference(d.reference_key, f'https://example.invalid/detail/{i}',
                                 'Fiktiv', 1, 'configured') for i, d in enumerate(details, 1))


def compare(details, observed, statuses=None, **kwargs):
    sample = DetailSample(len(details), len(details), tuple(details))
    return compare_weekly_presence(references(details), sample, observed,
                                   statuses or {w: 'ok' for w in observed},
                                   start=kwargs.get('start', START), end=kwargs.get('end', END))


def test_detects_wrong_week_even_when_global_course_sets_match():
    details = (detail('A', [START]), detail('B', [START+timedelta(days=7)]))
    result = compare(details, {W0: set(), W1: {'A', 'B'}})
    assert result['matched_course_weeks'] == 1
    assert result['expected_course_weeks'] == 2
    assert [(r['detail_number'], r['iso_year'], r['iso_week']) for r in result['missing_from_week_view']] == [(1, 2026, 53)]
    assert [(r['detail_number'], r['iso_year'], r['iso_week']) for r in result['observed_without_expected_occurrence']] == [(1, 2027, 1)]
    assert not result['comparable_pairs_match'] and not result['complete']
    assert result['weeks'][0]['missing_count'] == 1
    assert result['weeks'][1]['unexpected_count'] == 1
    assert sum(w['matched_course_weeks'] for w in result['weeks']) == result['matched_course_weeks']
    for private in ('FIKTIVER TITEL', 'example.invalid', 'DEMO-RAUM', 'DEMO-LEHRPERSON'):
        assert private not in json.dumps(result)


def test_multiple_occurrences_in_same_week_are_one_presence():
    result = compare((detail('A', [START, START+timedelta(days=1)]),), {W0: {'A'}})
    assert result['matched_course_weeks'] == result['expected_course_weeks'] == 1
    assert result['comparable_pairs_match'] and not result['complete']


def test_local_date_is_used_across_utc_and_iso_year_boundary():
    source = detail('A', [START+timedelta(days=7)], clock=time(0, 15))
    assert source.preview.occurrences[0].starts_at.startswith('2027-01-03')
    result = compare((source,), {W0: set(), W1: {'A'}})
    assert result['matched_course_weeks'] == 1 and result['comparable_pairs_match']


def test_visible_cancelled_only_week_is_reviewed_separately():
    result = compare((detail('A', [START], cancelled=(START,)),), {W0: {'A'}})
    assert result['expected_course_weeks'] == 0
    assert not result['observed_without_expected_occurrence']
    assert len(result['observed_cancellation_only']) == 1
    assert result['observed_cancellation_only'][0]['detail_requires_review']
    assert result['review_details'] == [1]


def test_cancellation_does_not_hide_other_expected_date_in_same_week():
    result = compare((detail('A', [START, START+timedelta(days=1)], cancelled=(START,)),), {W0: set()})
    assert len(result['missing_from_week_view']) == 1
    assert not result['observed_cancellation_only']


def test_weekend_only_dates_are_excluded_from_weekday_presence():
    result = compare((detail('A', [START+timedelta(days=6)]),), {W0: {'A'}})
    assert result['weekend_occurrence_count'] == 1
    assert result['expected_course_weeks'] == 0
    assert len(result['observed_weekend_only']) == 1
    assert not result['observed_without_expected_occurrence'] and not result['complete']


def test_unvisited_weeks_are_not_reported_as_missing_events():
    result = compare((detail('A', [START+timedelta(days=7)]),), {W0: set()})
    assert result['unobserved_expected_weeks'] == [W1]
    assert not result['missing_from_week_view']


def test_partial_boundary_week_is_not_compared():
    result = compare((detail('A', [START+timedelta(days=2)]),), {W0: {'A'}, W1: set()},
                     start=START+timedelta(days=1))
    assert result['partial_boundary_weeks'] == [W0]
    assert result['compared_weeks'] == [W1]
    assert not result['observed_without_expected_occurrence']


def test_only_partial_week_cannot_claim_matching_pairs():
    result = compare((detail('A', [START]),), {W0: {'A'}}, end=START+timedelta(days=1))
    assert not result['evaluated'] and result['comparable_pairs_match'] is None


@pytest.mark.parametrize('week_status', ['empty_unverified', 'notes_require_review'])
def test_week_review_status_is_retained_on_mismatch(week_status):
    result = compare((detail('A', [START], note='Raum X9.8.76'),), {W0: set()}, {W0: week_status})
    assert result['missing_from_week_view'][0]['week_status'] == week_status
    assert result['missing_from_week_view'][0]['detail_requires_review']


def test_blocked_details_are_not_assumed_empty():
    blocked = DetailResult('B', 1, 'normalization_requires_review', None)
    result = compare((detail('A', [START]), blocked), {W0: {'A', 'B'}})
    assert result['blocked_details'] == [2]
    assert not result['observed_without_expected_occurrence']
    assert result['normalizable_details'] == 1


def test_only_blocked_details_cannot_claim_matching_pairs():
    result = compare((DetailResult('A', 1, 'normalization_requires_review', None),), {W0: {'A'}})
    assert not result['evaluated'] and result['comparable_pairs_match'] is None


@pytest.mark.parametrize('kind', ['partial', 'wrong_identity', 'unknown_observed', 'missing_status'])
def test_incomplete_or_conflicting_input_is_rejected(kind):
    details = (detail('A', [START]),)
    refs = references(details)
    sample = DetailSample(1, 1, details)
    observed, statuses = {W0: {'A'}}, {W0: 'ok'}
    if kind == 'partial':
        sample = replace(sample, reference_count=2)
    elif kind == 'wrong_identity':
        sample = replace(sample, details=(replace(details[0], reference_key='B'),))
    elif kind == 'unknown_observed':
        observed = {W0: {'B'}}
    else:
        statuses = {}
    with pytest.raises(DetailImportError):
        compare_weekly_presence(refs, sample, observed, statuses, start=START, end=END)


@pytest.fixture
def detail_workflow(workflow, monkeypatch):
    original = SourceClient.fetch
    markup = (Path(__file__).parent/'fixtures/course_detail.html').read_text()
    calls = []
    state = {'fail_number': None, 'semester': 'WiSe 2025/26'}
    def fetch(self, url=None, **kwargs):
        if url and urlsplit(url).path == '/detail':
            calls.append(url)
            if len(calls) == state['fail_number']:
                raise SourceFetchError('PRIVATE')
            return SourceDocument(markup.replace('WiSe 2025/26', state['semester']), url)
        return original(self, url, **kwargs)
    monkeypatch.setattr(SourceClient, 'fetch', fetch)
    return calls, state


def run_details(**kwargs):
    arguments = dict(query='Fiktiv', title='Fiktives Studium', start=START, end=END,
                     identity_policy=POLICY, details=True, semester='WiSe 2025/26',
                     study_key='DEMO', regulations_key='DEMO-PO')
    arguments.update(kwargs)
    with SourceClient('https://example.invalid/start') as client:
        return run_view_comparison(client, **arguments)


def test_details_are_deduplicated_across_views_and_weeks(detail_workflow):
    calls, _ = detail_workflow
    report = run_details()
    assert len(calls) == report['checked_details'] == 4
    assert len(set(calls)) == 4
    assert report['schema_version'] == 3 and report['weekly_presence']['evaluated']
    assert report['normalization_summary']['preview_count'] == 4
    assert 'occurrence_fields_unverified' in report['blockers']
    assert 'detail_content_unchecked' not in report['blockers']
    assert not report['complete'] and not report['published']


@pytest.mark.parametrize('kind', ['fetch', 'semester', 'budget'])
def test_detail_failure_discards_partial_comparison(detail_workflow, kind):
    calls, state = detail_workflow
    if kind == 'fetch':
        state['fail_number'] = 3
    elif kind == 'semester':
        state['semester'] = 'FIKTIV FALSCH'
    report = run_details(detail_budget=2 if kind == 'budget' else 80)
    assert report['status'] == 'failed' and report['stage'] == 'details'
    assert report['weekly_presence'] is None and report['comparison'] is None
    assert report['checked_details'] == 0 and report['review_summary'] is None
    assert not report['comparison_evaluated'] and not report['complete']
    assert 'PRIVATE' not in json.dumps(report)
    if kind == 'budget':
        assert not calls


@pytest.mark.parametrize('kwargs', [{'semester': None}, {'study_key': ''}, {'regulations_key': ''},
                                     {'detail_budget': True}, {'detail_budget': 101}])
def test_invalid_detail_context_fails_before_network(workflow, kwargs):
    with pytest.raises(DetailImportError):
        run_details(**kwargs)
    assert not workflow['calls']


def test_cli_detail_context_from_environment_and_preview_unchanged(detail_workflow, monkeypatch, tmp_path):
    for name, value in {'LSF_STUDY_QUERY': 'Fiktiv', 'LSF_STUDY_TITLE': 'Fiktives Studium',
                        'LSF_SEMESTER': 'WiSe 2025/26', 'LSF_STUDY_KEY': 'DEMO',
                        'LSF_REGULATIONS_KEY': 'DEMO-PO'}.items():
        monkeypatch.setenv(name, value)
    filename = tmp_path/'previous.preview.json'
    filename.write_text('Fiktiver vorheriger Stand')
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo', 'PREVIEW_FILE': str(filename)})
    result = app.test_cli_runner().invoke(args=['source-coverage-check', '--start', '2026-12-28',
                                              '--end', '2027-01-10', '--all-weeks', '--details', '--json'])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report['checked_details'] == 4 and report['weekly_presence']['evaluated']
    assert not report['complete'] and filename.read_text() == 'Fiktiver vorheriger Stand'
    for private in ('FIKTIVER', 'example.invalid', 'DEMO-PO', 'WiSe', 'record='):
        assert private not in result.output


@pytest.mark.parametrize('kind', ['duplicate', 'unconfigured'])
def test_detail_selection_rejected_before_fetch(kind, monkeypatch):
    sources = references((detail('A', [START]),))
    if kind == 'duplicate':
        sources = sources + sources
    else:
        sources = (replace(sources[0], identity_scope='run'),)
    def forbidden(*a, **kw):
        pytest.fail('Invalid detail selection must not fetch')
    monkeypatch.setattr('backend.importer.presence.fetch_detail_sample', forbidden)
    with pytest.raises(DetailImportError):
        fetch_comparison_details(None, sources, semester='DEMO-Semester', study_key='STUDY',
                                 regulations_key='PO', budget=80)


def test_failed_week_cannot_be_compared_as_an_empty_week():
    with pytest.raises(DetailImportError):
        compare((detail('A', [START]),), {W0: set()}, {W0: 'failed'})


def test_missing_detail_flag_rejects_explicit_detail_context_before_network(workflow):
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-coverage-check', '--query', 'Fiktiv',
                                              '--title', 'Fiktives Studium', '--start', '2026-12-28',
                                              '--end', '2027-01-10', '--all-weeks', '--semester', 'DEMO-Semester'])
    assert result.exit_code == 1 and 'benötigen --details' in result.output
    assert not workflow['calls']
