from dataclasses import replace
from datetime import date, time
import json

import pytest

from backend import create_app
from backend.importer.details import DetailImportError, DetailResult, DetailSample
from backend.parser.course import CourseDetail, ScheduleSeries
from backend.parser.normalize import CourseContext, normalize_course
from backend.preview import save_preview_file, load_preview_file


@pytest.fixture
def sample():
    course = CourseDetail(None, '<script>alert(1)</script> Fiktiver Kurs', None, 'Demo', 'DEMO-Semester',
                          (ScheduleSeries(6, time(0, 15), time(1), date(2026, 10, 25), date(2026, 10, 25),
                                          'Einzel', 'DEMO-Raum', 'DEMO-Lehrperson', None, None, None),), ())
    preview = normalize_course(course, CourseContext('demo', 'study', 'rules', 'DEMO-Semester'))
    return DetailSample(2, 2, (DetailResult('demo', 1, 'preview', preview),
                              DetailResult('blocked', 1, 'needs_review', None)))


def test_preview_roundtrip_and_web_escaping(tmp_path, sample):
    path = tmp_path / 'test.preview.json'
    save_preview_file(path, sample, 'DEMO-Semester')
    data, status = load_preview_file(path)
    assert status == 'ready' and data['complete'] is False
    assert data['blocked_details'] == 1
    assert data['events'][0]['day'] == '25.10.2026'
    assert data['events'][0]['time'] == '00:15–01:00'
    assert 'reference_key' not in path.read_text(encoding='utf-8')
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(path)})
    client = app.test_client()
    result = client.get('/vorschau')
    html = result.get_data(as_text=True)
    assert result.status_code == 200
    assert 'Unvollständig' in html and 'kein freigegebener Archivstand' in html
    assert '1 blockiert' in html and 'Letzte erfolgreiche Sicherung: noch keine.' in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'DEMO-Raum' in html and 'DEMO-Lehrperson' in html
    assert result.headers['Cache-Control'] == 'no-store'
    assert client.get('/vorschau?week=2026-W43').status_code == 200
    assert client.get('/vorschau?week=2026-W01').status_code == 400
    assert '/vorschau' in client.get('/').get_data(as_text=True)


@pytest.mark.parametrize('failure', ['empty', 'partial', 'replace'])
def test_failed_or_empty_write_preserves_previous_file(tmp_path, sample, monkeypatch, failure):
    path = tmp_path / 'test.preview.json'
    save_preview_file(path, sample, 'DEMO-Semester')
    old = path.read_bytes()
    if failure == 'empty':
        sample = DetailSample(1, 1, (DetailResult('blocked', 1, 'needs_review', None),))
    elif failure == 'partial':
        sample = replace(sample, reference_count=3)
    else:
        def fail(*args):
            raise OSError('PRIVATE PATH')
        monkeypatch.setattr('backend.preview.os.replace', fail)
    with pytest.raises(DetailImportError) as error:
        save_preview_file(path, sample, 'DEMO-Semester')
    assert 'PRIVATE' not in str(error.value)
    assert path.read_bytes() == old
    assert not list(tmp_path.glob('.preview-*'))


@pytest.mark.parametrize('content', ['broken', '{"complete":true}', '[]', 'x' * 5_000_001], ids=['json', 'complete', 'array', 'oversize'])
def test_invalid_preview_is_not_rendered(tmp_path, content):
    path = tmp_path / 'test.preview.json'
    path.write_text(content, encoding='utf-8')
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(path)})
    html = app.test_client().get('/vorschau').get_data(as_text=True)
    assert 'konnte nicht gelesen werden' in html
    assert str(path) not in html


def test_no_preview_and_no_network(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Web request must not access source')
    monkeypatch.setattr('backend.importer.http.SourceClient.fetch', forbidden)
    for path in ('', str(tmp_path / 'absent.preview.json')):
        app = create_app({'TESTING': True, 'PREVIEW_FILE': path})
        html = app.test_client().get('/vorschau').get_data(as_text=True)
        assert 'Noch keine lesbare Import-Vorschau' in html


def test_save_preview_option_requires_configuration_before_network():
    app = create_app({'TESTING': True, 'PREVIEW_FILE': ''})
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--query', 'Demo', '--title', 'Demo', '--save-preview'])
    assert result.exit_code == 1 and 'Vorschau benötigt' in result.output

@pytest.mark.parametrize('fail', [False, True])
def test_cli_saves_only_after_successful_detail_fetch(tmp_path, sample, monkeypatch, fail):
    path = tmp_path / 'test.preview.json'
    for name in ('search_study', 'follow_named_result', 'submit_labeled_search'):
        monkeypatch.setattr('backend.cli.' + name, lambda *args, **kwargs: None)
    monkeypatch.setattr('backend.cli.audit_semester_views', lambda *args, **kwargs: ())
    def fetch(*args, **kwargs):
        if fail:
            raise DetailImportError('PRIVATE')
        return sample
    monkeypatch.setattr('backend.cli.fetch_semester_details', fetch)
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(path),
                      'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--query', 'Demo', '--title', 'Demo',
                                              '--details', '--save-preview', '--semester', 'DEMO-Semester',
                                              '--study-key', 'demo', '--regulations-key', 'demo', '--json'])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report['status'] == ('failed' if fail else 'needs_review')
    assert path.exists() is not fail
    assert not report['published'] and not report['complete']
    assert 'PRIVATE' not in result.output and 'Fiktiver' not in result.output


def test_week_view_has_seven_days_and_list_remains_available(tmp_path, sample):
    from bs4 import BeautifulSoup
    path = tmp_path / 'test.preview.json'
    save_preview_file(path, sample, 'DEMO-Semester')
    client = create_app({'TESTING': True, 'PREVIEW_FILE': str(path)}).test_client()
    soup = BeautifulSoup(client.get('/vorschau').data, 'html.parser')
    days = soup.select('.preview-day')
    assert len(days) == 7
    assert 'Montag' in days[0].get_text() and 'Sonntag' in days[-1].get_text()
    assert len(days[-1].select('.week-event')) == 1
    assert '00:15' in days[-1].get_text()
    assert len(soup.select('.day-empty')) == 6
    assert 'Abdeckung ungeprüft' in days[0].get_text()
    assert not soup.select('a[rel="prev"], a[rel="next"]')
    listing = BeautifulSoup(client.get('/vorschau?view=list').data, 'html.parser')
    assert len(listing.select('.preview-events li')) == 1
    assert not listing.select('.preview-week')
    assert client.get('/vorschau?view=invalid').status_code == 400


def test_week_navigation_preserves_mode_and_handles_year_boundary(tmp_path, sample):
    from bs4 import BeautifulSoup
    path = tmp_path / 'test.preview.json'
    save_preview_file(path, sample, 'DEMO-Semester')
    data = json.loads(path.read_text(encoding='utf-8'))
    template = data['events'][0]
    data['events'] = [dict(template, start=day + 'T10:00:00+00:00', end=day + 'T11:00:00+00:00')
                      for day in ('2025-12-22', '2025-12-29', '2026-01-12')]
    path.write_text(json.dumps(data), encoding='utf-8')
    client = create_app({'TESTING': True, 'PREVIEW_FILE': str(path)}).test_client()
    soup = BeautifulSoup(client.get('/vorschau?view=week&week=2026-W01').data, 'html.parser')
    assert '29.12.2025 bis 04.01.2026' in soup.get_text()
    assert 'week=2025-W52' in soup.select_one('a[rel="prev"]')['href']
    assert 'week=2026-W03' in soup.select_one('a[rel="next"]')['href']
    assert 'view=week' in soup.select_one('a[rel="next"]')['href']
    assert 'Wochen ohne erfasste Termine' in soup.get_text()
    listing = BeautifulSoup(client.get('/vorschau?view=list').data, 'html.parser')
    assert len(listing.select('.preview-events li')) == 3


@pytest.mark.parametrize('today,expected', [(date(2025, 12, 29), '2026-W01'),
                                          (date(2025, 12, 1), '2025-W52'),
                                          (date(2026, 1, 5), '2026-W03'),
                                          (date(2026, 2, 1), '2026-W03')])
def test_default_week_uses_current_next_or_last_recorded_week(today, expected):
    from backend.preview_calendar import default_week
    assert default_week(['2025-W52', '2026-W01', '2026-W03'], today) == expected
    assert default_week([], today) == ''


def test_calendar_keeps_overlapping_events_and_sorts_by_absolute_time():
    from backend.preview_calendar import week_days
    events = [dict(title='Demo B', start='2026-10-25T01:15:00+00:00'),
              dict(title='Demo A', start='2026-10-25T00:30:00+00:00'),
              dict(title='Demo C', start='2026-10-25T00:30:00+00:00')]
    days = week_days('2026-W43', events)
    assert [event['title'] for event in days[6]['events']] == ['Demo A', 'Demo C', 'Demo B']
    assert all(not day['events'] for day in days[:6])
