"""Fiktiver Import bis zur Web-Ausgabe und eindeutigem Speicherstatus."""
import json

import pytest

from backend import create_app
from backend.importer.details import DetailImportError
from backend.preview import save_preview_file, load_preview_file
from tests.test_preview import sample


@pytest.mark.parametrize('failure', ['none', 'fetch', 'write'])
def test_saved_selection_imports_and_reports_actual_save(tmp_path, sample, monkeypatch, failure):
    filename = tmp_path / 'selection.preview.json'
    save_preview_file(filename, sample, 'DEMO-Semester', study_title='Fiktiver alter Studiengang')
    old = filename.read_bytes()
    values = {'LSF_STUDY_QUERY': 'Fiktive Suche', 'LSF_STUDY_TITLE': 'Fiktiver Studiengang (DEMO-PO)',
              'LSF_SEMESTER': 'DEMO-Semester', 'LSF_STUDY_KEY': 'demo', 'LSF_REGULATIONS_KEY': 'demo-po'}
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr('backend.cli.search_study', lambda client, query: query)
    def follow(client, results, *, title):
        assert results == values['LSF_STUDY_QUERY']
        assert title == values['LSF_STUDY_TITLE']
    monkeypatch.setattr('backend.cli.follow_named_result', follow)
    monkeypatch.setattr('backend.cli.submit_labeled_search', lambda *a, **kw: None)
    monkeypatch.setattr('backend.cli.audit_semester_views', lambda *a, **kw: ())
    def fetch(*a, **kw):
        assert kw['semester'] == values['LSF_SEMESTER']
        assert kw['study_key'] == values['LSF_STUDY_KEY']
        assert kw['regulations_key'] == values['LSF_REGULATIONS_KEY']
        if failure == 'fetch':
            raise DetailImportError('PRIVATE')
        return sample
    monkeypatch.setattr('backend.cli.fetch_semester_details', fetch)
    if failure == 'write':
        def fail(*args):
            raise OSError('PRIVATE')
        monkeypatch.setattr('backend.preview.os.replace', fail)
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(filename),
                      'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--details', '--save-preview', '--json'])
    assert result.exit_code == 1  # Speichern ist keine Archivfreigabe.
    report = json.loads(result.output)
    assert report['schema_version'] == 7
    assert report['preview_save'] == {'requested': True, 'saved': failure == 'none',
                                      'event_count': 1 if failure == 'none' else 0}
    assert report['status'] == ('needs_review' if failure == 'none' else 'failed')
    assert not report['complete'] and not report['published']
    assert 'PRIVATE' not in result.output and str(filename) not in result.output
    assert values['LSF_STUDY_TITLE'] not in result.output
    if failure != 'none':
        assert filename.read_bytes() == old
    else:
        # Ein Seitenaufruf darf weder Navigation noch Abruf erneut starten.
        def forbidden(*a, **kw):
            pytest.fail('Web request started an import')
        monkeypatch.setattr('backend.importer.http.SourceClient.fetch', forbidden)
        for route in ('/vorschau', '/vorschau?view=list'):
            response = app.test_client().get(route)
            assert response.status_code == 200
            html = response.get_data(as_text=True)
            assert values['LSF_STUDY_TITLE'] in html and '1 blockiert' in html
            assert 'Unvollständig' in html


def test_explicit_selection_overrides_environment(monkeypatch):
    for name in ('LSF_STUDY_QUERY', 'LSF_STUDY_TITLE'):
        monkeypatch.setenv(name, 'Fiktiver alter Wert')
    seen = []
    def search(client, query):
        seen.append(query)
    def follow(client, results, *, title):
        seen.append(title)
        raise DetailImportError('Testabbruch')
    monkeypatch.setattr('backend.cli.search_study', search)
    monkeypatch.setattr('backend.cli.follow_named_result', follow)
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--query', 'Fiktive neue Suche',
                                              '--title', 'Fiktiver neuer Titel', '--json'])
    report = json.loads(result.output)
    assert seen == ['Fiktive neue Suche', 'Fiktiver neuer Titel']
    assert report['preview_save'] == {'requested': False, 'saved': False, 'event_count': 0}


@pytest.mark.parametrize('title', [None, '', ' ', 42, 'X' * 201])
def test_optional_study_title_is_validated_without_losing_previous_file(tmp_path, sample, title):
    filename = tmp_path / 'selection.preview.json'
    save_preview_file(filename, sample, 'DEMO-Semester')
    old = filename.read_bytes()
    if title is None:
        data, status = load_preview_file(filename)
        assert status == 'ready' and 'study_title' not in data
        app = create_app({'TESTING': True, 'PREVIEW_FILE': str(filename)})
        assert 'noch nicht hinterlegt' in app.test_client().get('/vorschau').get_data(as_text=True)
    else:
        with pytest.raises(DetailImportError):
            save_preview_file(filename, sample, 'DEMO-Semester', study_title=title)
        assert filename.read_bytes() == old


def test_study_title_is_escaped_in_web_view(tmp_path, sample):
    filename = tmp_path / 'selection.preview.json'
    title = '<script>PRIVATE</script> Fiktiver Studiengang'
    save_preview_file(filename, sample, 'DEMO-Semester', study_title=title)
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(filename)})
    html = app.test_client().get('/vorschau').get_data(as_text=True)
    assert title not in html
    assert '&lt;script&gt;PRIVATE&lt;/script&gt; Fiktiver Studiengang' in html


@pytest.mark.parametrize('missing', ['LSF_STUDY_QUERY', 'LSF_STUDY_TITLE', 'LSF_SEMESTER',
                                     'LSF_STUDY_KEY', 'LSF_REGULATIONS_KEY'])
def test_incomplete_saved_selection_fails_before_network(tmp_path, monkeypatch, missing):
    values = {'LSF_STUDY_QUERY': 'Fiktive Suche', 'LSF_STUDY_TITLE': 'Fiktiver Titel',
              'LSF_SEMESTER': 'DEMO-Semester', 'LSF_STUDY_KEY': 'demo', 'LSF_REGULATIONS_KEY': 'demo-po'}
    for name, value in values.items():
        monkeypatch.setenv(name, value if name != missing else '')
    def forbidden(*a, **kw):
        pytest.fail('Incomplete selection must not access source')
    monkeypatch.setattr('backend.cli.search_study', forbidden)
    app = create_app({'TESTING': True, 'PREVIEW_FILE': str(tmp_path / 'test.preview.json'),
                      'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--details', '--save-preview', '--json'])
    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)
    assert not (tmp_path / 'test.preview.json').exists()


def test_saved_detail_context_does_not_block_view_only_check(monkeypatch):
    for name, value in {'LSF_STUDY_QUERY': 'Fiktive Suche', 'LSF_STUDY_TITLE': 'Fiktiver Titel',
                        'LSF_SEMESTER': 'DEMO-Semester', 'LSF_STUDY_KEY': 'demo',
                        'LSF_REGULATIONS_KEY': 'demo-po'}.items():
        monkeypatch.setenv(name, value)
    for name in ('search_study', 'follow_named_result', 'submit_labeled_search'):
        monkeypatch.setattr('backend.cli.' + name, lambda *a, **kw: None)
    monkeypatch.setattr('backend.cli.audit_semester_views', lambda *a, **kw: ())
    def forbidden(*a, **kw):
        pytest.fail('View-only check must not fetch details')
    monkeypatch.setattr('backend.cli.fetch_semester_details', forbidden)
    app = create_app({'TESTING': True, 'LSF_BASE_URL': 'https://example.invalid/start',
                      'LSF_ID_PARAMETER': 'record', 'LSF_ID_NAMESPACE': 'demo'})
    report = json.loads(app.test_cli_runner().invoke(args=['source-semester-check', '--json']).output)
    assert not report['details_requested'] and report['status'] == 'needs_review'
    # Explizite Detailparameter ohne --details bleiben Eingabefehler.
    result = app.test_cli_runner().invoke(args=['source-semester-check', '--semester', 'DEMO-Semester'])
    assert result.exit_code == 1 and 'benötigen --details' in result.output
