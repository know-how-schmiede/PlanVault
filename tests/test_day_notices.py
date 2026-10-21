"""Tageshinweise liefern Kontext, niemals eine automatische Ausfallfreigabe."""
import json

import pytest

from backend.importer.comparison import run_view_comparison
from backend.importer.details import DetailSample, DetailImportError
from backend.importer.http import SourceClient
from backend.importer.notices import DayNotice, classify_day_notice
from backend.importer.presence import compare_weekly_presence
from backend.importer.weeks import inspect_week, read_week_menu
from tests.test_weeks import doc, html
from tests.test_weekly_presence import detail, references, START, END, W0, W1
from tests.test_view_comparison import workflow, POLICY


def compare(days, notices, *, cancelled=()):
    source = detail('A', days, cancelled=cancelled)
    return compare_weekly_presence(references((source,)), DetailSample(1, 1, (source,)),
                                   {W0: set()}, {W0: 'notes_require_review'},
                                   start=START, end=END, day_notices=notices)


@pytest.mark.parametrize('text,kind', [('Weihnachtsferien', 'christmas_break'),
                                      ('Heilige Drei Könige', 'epiphany'),
                                      ('unbenannt', 'unnamed')])
def test_exact_verified_labels_become_codes_and_status_stays_review(text, kind):
    document = doc(html(notice=' ' + text))
    result = inspect_week(document, read_week_menu(document).choices[0])
    assert result.status == 'notes_require_review'
    assert len(result.day_notices) == 5
    assert result.day_notices[0] == DayNotice('2026-12-28', kind)
    assert text not in repr(result)


@pytest.mark.parametrize('text', ['Keine Weihnachtsferien', 'Weihnachtsferien ab 12 Uhr',
                                  'Weihnachtsferien außer Labor', 'Heilige Drei Könige: FIKTIV',
                                  'PRIVATE https://example.invalid/secret', '<script>PRIVATE</script>',
                                  'weihnachtsferien', 'FIKTIVE FREMDANGABE'])
def test_unknown_extended_or_negated_notice_is_not_a_rule(text):
    assert classify_day_notice(text) == 'unclassified'


@pytest.mark.parametrize('day,kind', [('31.12.2026', 'christmas_break'), ('2026-02-31', 'epiphany'),
                                     ('20261228', 'christmas_break'), ('2026-12-28', 'PRIVATE'),
                                     (None, 'unclassified'), ('2026-12-28', []), ('2026-12-28', None)])
def test_invalid_day_notice_is_rejected_without_echo(day, kind):
    with pytest.raises(ValueError) as error:
        DayNotice(day, kind)
    assert 'PRIVATE' not in str(error.value)


def test_all_expected_dates_known_notice_keeps_the_mismatch():
    result = compare([START], {W0: (DayNotice(START.isoformat(), 'christmas_break'),)})
    row = result['missing_from_week_view'][0]
    assert row['notice_assessment'] == 'all_expected_dates_with_known_notice'
    assert row['expected_local_dates'] == ['2026-12-28']
    assert row['expected_day_notices'] == [{'local_date': '2026-12-28', 'kind': 'christmas_break'}]
    assert result['missing_notice_context_counts'][row['notice_assessment']] == 1
    assert not result['comparable_pairs_match'] and not result['complete']
    assert result['expected_course_weeks'] == 1
    assert result['day_notice_policy'] == 'context_only_no_automatic_exclusion'


def test_notice_on_other_day_does_not_explain_a_mismatch():
    result = compare([START], {W0: (DayNotice('2026-12-29', 'christmas_break'),)})
    row = result['missing_from_week_view'][0]
    assert row['notice_assessment'] == 'no_notice_on_expected_dates'
    assert row['expected_day_notices'] == []


def test_some_expected_days_annotated_does_not_cover_the_whole_week():
    from datetime import timedelta
    result = compare([START, START+timedelta(days=1)],
                     {W0: (DayNotice('2026-12-28', 'christmas_break'),)})
    assert result['missing_from_week_view'][0]['notice_assessment'] == 'some_expected_dates_with_known_notice'
    assert len(result['missing_from_week_view'][0]['expected_local_dates']) == 2


def test_unclassified_notice_is_preserved_without_its_text():
    result = compare([START], {W0: (DayNotice('2026-12-28', 'unclassified'),)})
    assert result['missing_from_week_view'][0]['notice_assessment'] == 'unclassified_notice_on_expected_date'
    assert result['missing_from_week_view'][0]['expected_day_notices'][0]['kind'] == 'unclassified'


def test_no_notices_differs_from_unavailable_notice_evidence():
    result = compare([START], {W0: ()})
    assert result['missing_from_week_view'][0]['notice_assessment'] == 'no_notice_on_expected_dates'
    result = compare([START], None)
    assert result['missing_from_week_view'][0]['notice_assessment'] == 'day_notice_evidence_unavailable'


def test_cancelled_date_is_not_in_the_expected_notice_context():
    from datetime import timedelta
    result = compare([START, START+timedelta(days=1)],
                     {W0: (DayNotice('2026-12-28', 'christmas_break'),)}, cancelled=(START,))
    row = result['missing_from_week_view'][0]
    assert row['expected_local_dates'] == ['2026-12-29']
    assert row['notice_assessment'] == 'no_notice_on_expected_dates'


def test_duplicate_occurrences_on_one_day_do_not_inflate_notice_counts():
    result = compare([START, START], {W0: (DayNotice('2026-12-28', 'christmas_break'),)})
    assert len(result['missing_from_week_view']) == 1
    assert result['missing_from_week_view'][0]['expected_local_dates'] == ['2026-12-28']
    assert sum(result['missing_notice_context_counts'].values()) == 1
    assert result['weeks'][0]['missing_notice_context_counts'] == result['missing_notice_context_counts']


@pytest.mark.parametrize('notices', [{W1: ()},
    {W0: (DayNotice('2027-01-04', 'epiphany'),)},
    {W0: (DayNotice('2027-01-03', 'christmas_break'),)},
    {W0: (DayNotice('2026-12-28', 'christmas_break'), DayNotice('2026-12-28', 'unclassified'))},
    {W0: ('PRIVATE',)}])
def test_wrong_week_weekend_duplicate_or_raw_notice_is_rejected(notices):
    with pytest.raises(DetailImportError):
        compare([START], notices)


def test_notice_codes_flow_from_week_parser_to_detail_diagnosis(workflow, monkeypatch):
    workflow['notices'][0] = ' Weihnachtsferien'
    def sample(client, refs, **kwargs):
        return DetailSample(len(refs), len(refs), tuple(detail(r.key, [START]) for r in refs))
    monkeypatch.setattr('backend.importer.comparison.fetch_comparison_details', sample)
    with SourceClient('https://example.invalid/start') as client:
        report = run_view_comparison(client, query='Fiktiv', title='Fiktives Studium', start=START,
                                     end=END, identity_policy=POLICY, details=True, semester='DEMO-Semester',
                                     study_key='STUDY', regulations_key='PO')
    assert report['schema_version'] == 4
    assert len(report['checked_weeks'][0]['day_notices']) == 5
    presence = report['weekly_presence']
    assert len(presence['missing_from_week_view']) == 2
    assert presence['missing_notice_context_counts']['all_expected_dates_with_known_notice'] == 2
    assert 'weekly_presence_mismatch' in report['blockers']
    assert 'weeks_require_review' in report['blockers']
    assert not report['complete'] and not report['published']
    text = json.dumps(report)
    for private in ('Weihnachtsferien', 'FIKTIVER', 'PRIVATE', 'example.invalid', 'DEMO-RAUM'):
        assert private not in text



def test_unnamed_label_is_not_a_known_calendar_meaning():
    from backend.importer.notices import KNOWN_NOTICE_KINDS
    assert classify_day_notice('unbenannt') == 'unnamed'
    assert 'unnamed' not in KNOWN_NOTICE_KINDS
    result = compare([START], {W0: (DayNotice('2026-12-28', 'unnamed'),)})
    row = result['missing_from_week_view'][0]
    assert row['notice_assessment'] == 'unnamed_notice_on_expected_date'
    assert row['expected_day_notices'] == [{'local_date': '2026-12-28', 'kind': 'unnamed'}]
    assert result['missing_notice_context_counts']['unnamed_notice_on_expected_date'] == 1
    assert result['missing_notice_context_counts']['all_expected_dates_with_known_notice'] == 0
    assert not result['comparable_pairs_match'] and not result['complete']


@pytest.mark.parametrize('label', ['Unbenannt', 'unbenannt Ferien', 'nicht unbenannt', 'unbenannt außer Labor'])
def test_only_exact_unnamed_label_is_recognized(label):
    assert classify_day_notice(label) == 'unclassified'


def test_known_and_unnamed_days_remain_only_partially_classified():
    from datetime import timedelta
    result = compare([START, START+timedelta(days=1)],
                     {W0: (DayNotice('2026-12-28', 'christmas_break'),
                            DayNotice('2026-12-29', 'unnamed'))})
    row = result['missing_from_week_view'][0]
    assert row['notice_assessment'] == 'some_expected_dates_with_known_notice'
    assert [n['kind'] for n in row['expected_day_notices']] == ['christmas_break', 'unnamed']
    assert not result['comparable_pairs_match'] and not result['complete']


@pytest.mark.parametrize('label,kind,blocker', [
    ('unbenannt', 'unnamed', 'unnamed_day_notices_require_review'),
    ('PRIVATE unbekannt', 'unclassified', 'unclassified_day_notices_require_review'),
])
def test_unresolved_source_days_are_reported_without_detail_fetch(workflow, label, kind, blocker):
    workflow['notices'][1] = ' ' + label
    with SourceClient('https://example.invalid/start') as client:
        report = run_view_comparison(client, query='Fiktiv', title='Fiktives Studium', start=START,
                                     end=END, identity_policy=POLICY)
    assert report['schema_version'] == 4 and report['weekly_presence'] is None
    assert report['unresolved_day_notices'] == [
        {'local_date': f'2027-01-0{n}', 'kind': kind} for n in range(4, 9)]
    assert blocker in report['blockers'] and 'weeks_require_review' in report['blockers']
    assert not report['complete'] and not report['published']
    text = json.dumps(report)
    assert label not in text and 'PRIVATE' not in text


def test_cli_explains_unnamed_source_days_in_text(workflow):
    from backend import create_app
    workflow['notices'][1] = ' unbenannt'
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-coverage-check', '--query', 'Fiktiv',
                                              '--title', 'Fiktives Studium', '--start', '2026-12-28',
                                              '--end', '2027-01-10', '--all-weeks'])
    assert result.exit_code == 1
    assert 'unbenannte Tageshinweise' in result.output
    assert 'unnamed_day_notices_require_review' in result.output
