"""Fiktiver Ansichtsabgleich einschließlich Jahreswechsel, Lücken und Fehlern."""
from datetime import date, timedelta
import json
from urllib.parse import urlsplit

import pytest

from backend import create_app
from backend.importer.comparison import run_view_comparison, ComparisonInputError, compare_references
from backend.importer.details import CourseReference, DetailImportError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.identity import SourceIdentityPolicy

START, END = date(2026, 12, 28), date(2027, 1, 10)
POLICY = SourceIdentityPolicy('record', 'PRIVATE-NAMESPACE')
DAYS = ('Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag')


def page(selected='w0', refs=(1, 2), notice='', changed=False, caption_suffix='', broken=False):
    options = [('w0', 'Woche: 53 28.12.2026 ---- 03.01.2027'),
               ('w1', 'Woche: 1 04.01.2027 ---- 10.01.2027'),
               ('all', 'Semesteransicht'), ('special', 'Semesterzeitansicht nur Block/Einzeltermine')]
    if changed:
        options[1] = ('w1', 'Woche: 2 11.01.2027 ---- 17.01.2027')
    html = '<form action="/view" method="post"><select name="demo-view">'
    html += ''.join(f'<option value="{value}" {"selected" if value == selected else ""}>{label}</option>'
                    for value, label in options)
    html += '</select><input type="submit" name="show" value="anzeigen"></form><table><tr>'
    if selected.startswith('w'):
        monday = START + timedelta(days=7 * int(selected[1:]))
        html += ''.join(f'<th>{name} {monday+timedelta(days=i):%d.%m.%Y}{notice}</th>' for i, name in enumerate(DAYS))
    else:
        html += ''.join(f'<th>{name}</th>' for name in DAYS)
    html += '</tr></table>'
    for ref in refs:
        html += (f'<table><tr><td class="plan5a"><a href="/detail?record={ref}&session={selected}">'
                 f'FIKTIVER-KURS-{ref}{caption_suffix}</a></td></tr>' +
                 '<tr><td>DEMO</td></tr>' * (6 if broken else 7) + '</table>')
    return html


@pytest.fixture
def workflow(monkeypatch):
    state = {'calls': [], 'weeks': [(1, 4), (2,)], 'semester': (1, 2, 3), 'special': (2,),
             'notices': ['', ''], 'failure': None, 'changed': None,
             'caption_suffix': '', 'broken': False}
    entry = ('<form action="/search"><label for="study">Studiengang</label><input id="study" name="query">'
             '<input type="submit" name="find" value="Auswahl"></form>')
    selected = ('<form action="/plan"><label for="study">Studiengang</label><input id="study" readonly>'
                '<input name="selected" type="hidden" value="DEMO">'
                '<input type="submit" name="go" value="Suche starten"></form>')
    def fetch(self, url=None, **kwargs):
        path = urlsplit(url or 'https://example.invalid/start').path
        mode = dict(kwargs.get('form', ())).get('demo-view')
        state['calls'].append(mode or path)
        if mode and mode == state['failure']:
            raise SourceFetchError('PRIVATE https://example.invalid/secret')
        if path == '/start':
            html = entry
        elif path == '/search':
            html = '<a href="/selected">Fiktives Studium</a>'
        elif path == '/selected':
            html = selected
        elif path == '/plan':
            html = page()
        elif path == '/view':
            if mode.startswith('w'):
                i = int(mode[1:])
                html = page(mode, state['weeks'][i], state['notices'][i],
                            changed=mode == state['changed'], caption_suffix=state['caption_suffix'],
                            broken=state['broken'])
            else:
                html = page(mode, state['semester'] if mode == 'all' else state['special'])
        else:
            pytest.fail('Ansichtsabgleich darf keine Detailseite abrufen')
        return SourceDocument(html, url or 'https://example.invalid/start')
    monkeypatch.setattr(SourceClient, 'fetch', fetch)
    return state


def run(**kwargs):
    values = dict(query='Fiktiv', title='Fiktives Studium', start=START, end=END, identity_policy=POLICY)
    values.update(kwargs)
    with SourceClient('https://example.invalid/start') as client:
        return run_view_comparison(client, **values)


def test_compares_both_directions_and_deduplicates_session_links(workflow):
    report = run()
    comparison = report['comparison']
    assert comparison == {'semester_reference_count': 3, 'week_reference_count': 3,
                          'shared_reference_count': 2, 'only_in_weeks': [4],
                          'only_in_semester_views': [3], 'reference_sets_equal': False}
    assert report['period_weeks_verified'] and report['all_requested_weeks_observed']
    assert report['comparison_evaluated'] and report['stage'] == 'finished'
    assert report['missing_weeks'] == ()
    assert 'references_missing_from_semester_views' in report['blockers']
    assert 'semester_references_not_observed_in_weeks' in report['blockers']
    assert workflow['calls'][-4:] == ['all', 'special', 'w0', 'w1']
    assert not report['complete'] and not report['published'] and not report['weekend_coverage_verified']
    serialized = json.dumps(report)
    for secret in ('example.invalid', 'PRIVATE', 'FIKTIVER', 'record', 'session', 'Fiktives Studium'):
        assert secret not in serialized


def test_equal_sets_do_not_mean_verified_semester(workflow):
    workflow['weeks'] = [(1, 2), (3,)]
    report = run()
    assert report['comparison']['reference_sets_equal']
    assert report['status'] == 'needs_review' and not report['complete']
    assert {'semester_extent_unverified', 'weekend_coverage_unverified', 'detail_content_unchecked',
            'study_context_unverified'} <= set(report['blockers'])


def test_partial_selection_never_turns_unobserved_targets_into_deleted_events(workflow):
    report = run(requested=((2026, 53),))
    assert report['missing_weeks'] == ((2027, 1),)
    assert report['all_requested_weeks_observed'] and not report['period_weeks_verified']
    assert report['comparison']['only_in_semester_views'] == [2, 3]
    assert 'missing_weeks' in report['blockers']


@pytest.mark.parametrize('empty', [False, True])
def test_holiday_notes_are_kept_and_later_weeks_still_observed(workflow, empty):
    workflow['notices'][0] = ' Fiktive Ferien'
    if empty:
        workflow['weeks'][0] = ()
    report = run()
    assert report['checked_weeks'][0]['status'] == 'notes_require_review'
    assert report['checked_weeks'][0]['reference_count'] == (0 if empty else 2)
    assert report['checked_weeks'][1]['status'] == 'ok'
    assert report['review_weeks'] == [(2026, 53)]
    assert report['all_requested_weeks_observed'] and not report['period_weeks_verified']
    assert 'weeks_require_review' in report['blockers']


def test_empty_week_is_not_a_confirmed_free_week(workflow):
    workflow['weeks'][0] = ()
    report = run()
    assert report['checked_weeks'][0]['status'] == 'empty_unverified'
    assert report['all_requested_weeks_observed'] and not report['period_weeks_verified']


def test_missing_source_week_is_reported_against_independent_period(workflow):
    report = run(end=END + timedelta(days=7))
    assert report['unavailable_weeks'] == [(2027, 2)]
    assert report['missing_weeks'] == ((2027, 2),)
    assert not report['all_requested_weeks_observed'] and not report['period_weeks_verified']
    assert 'requested_weeks_unavailable' in report['blockers']


def test_no_requested_week_available_does_not_confirm_coverage(workflow):
    report = run(start=END+timedelta(days=1), end=END+timedelta(days=7))
    assert not report['all_requested_weeks_observed']
    assert not report['period_weeks_verified']
    assert report['comparison'] is None and not report['comparison_evaluated']
    assert 'missing_weeks' in report['blockers']


@pytest.mark.parametrize('kind', ['network', 'menu', 'block', 'caption', 'semester'])
def test_failure_never_returns_successful_partial_comparison(workflow, kind):
    if kind == 'network':
        workflow['failure'] = 'w1'
    elif kind == 'menu':
        workflow['changed'] = 'w1'
    elif kind == 'block':
        workflow['broken'] = True
    elif kind == 'caption':
        workflow['caption_suffix'] = ' Konflikt'
    else:
        workflow['failure'] = 'special'
    report = run()
    assert report['status'] == 'failed'
    assert not report['comparison_evaluated'] and report['comparison'] is None
    assert not report['complete'] and not report['published']
    assert 'PRIVATE' not in json.dumps(report)
    if kind == 'block':
        assert report['failed_weeks'] == [(2026, 53)]
        assert 'w1' not in workflow['calls']


@pytest.mark.parametrize('kwargs', [
    {'week_budget': 1}, {'week_budget': True}, {'week_budget': 55}, {'identity_policy': None},
    {'requested': ()}, {'requested': ((2026, 53), (2026, 53))},
    {'requested': ((2027, 54),)}, {'requested': ((2027, True),)},
    {'requested': ((2027, 2),)}, {'requested': ([2026, 53],)},
    {'start': END, 'end': START}, {'start': 'PRIVATE'}, {'query': ''}, {'title': 'X' * 201},
])
def test_invalid_input_fails_before_any_request(workflow, kwargs):
    with pytest.raises(ComparisonInputError):
        run(**kwargs)
    assert workflow['calls'] == []


def test_comparison_refuses_unverified_identity():
    ref = CourseReference('demo', 'https://example.invalid/detail', 'Fiktiv', 1)
    with pytest.raises(DetailImportError):
        compare_references((ref,), ())


def test_cli_uses_saved_selection_and_does_not_change_web_preview(workflow, tmp_path, monkeypatch):
    monkeypatch.setenv('LSF_STUDY_QUERY', 'Fiktiv')
    monkeypatch.setenv('LSF_STUDY_TITLE', 'Fiktives Studium')
    preview = tmp_path / 'untouched.preview.json'
    preview.write_text('Fiktiver unveränderter Stand')
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo', 'PREVIEW_FILE': str(preview)})
    result = app.test_cli_runner().invoke(args=['source-coverage-check', '--start', '2026-12-28',
                                              '--end', '2027-01-10', '--all-weeks', '--json'])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report['comparison']['only_in_weeks'] == [4]
    assert preview.read_text() == 'Fiktiver unveränderter Stand'


@pytest.mark.parametrize('options', [[], ['--all-weeks', '--week', '2026-W53'],
                                      ['--week', 'PRIVATE'], ['--all-weeks', '--week-budget', '1']])
def test_cli_rejects_invalid_selection_before_network(workflow, options):
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-coverage-check', '--query', 'Fiktiv',
                                              '--title', 'Fiktives Studium', '--start', '2026-12-28',
                                              '--end', '2027-01-10', *options])
    assert result.exit_code != 0
    assert workflow['calls'] == []



def test_empty_semester_view_is_not_an_authoritative_empty_inventory(workflow):
    workflow['semester'] = ()
    report = run()
    assert report['views'][0]['status'] == 'empty_unverified'
    assert 'semester_view_empty_or_unverified' in report['blockers']
    assert not report['complete']


def test_network_failure_stops_later_weeks_and_lists_failed_week(workflow):
    workflow['failure'] = 'w0'
    report = run()
    assert report['failed_weeks'] == [(2026, 53)]
    assert report['missing_weeks'] == ((2027, 1),)
    assert 'w1' not in workflow['calls']
    assert not report['all_requested_weeks_observed']
