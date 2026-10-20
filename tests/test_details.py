from pathlib import Path
from types import SimpleNamespace

import pytest

from backend import create_app
from backend.importer.details import collect_course_references, fetch_detail_sample, DetailImportError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError


def block(href="/detail", title="Fiktive Veranstaltung"):
    return (f'<table><tr><td class="plan5a"><a href="{href}">{title}</a></td></tr>' +
            "<tr><td>Fiktive Angabe</td></tr>" * 3 +
            '<tr><td><a href="/room">Fiktiver Raum</a></td></tr>' +
            "<tr><td>Fiktive Angabe</td></tr>" * 3 + "</table>")


def doc(html):
    return SourceDocument(html, "https://example.invalid/plan")


@pytest.fixture
def client(monkeypatch):
    with SourceClient("https://example.invalid/start") as client:
        calls = []
        html = (Path(__file__).parent / "fixtures/course_detail.html").read_text(encoding="utf-8")
        def fetch(url):
            calls.append(url)
            return SourceDocument(html, url)
        monkeypatch.setattr(client, "fetch", fetch)
        yield client, calls


def sample(client, refs, **kwargs):
    return fetch_detail_sample(client, refs, semester="WiSe 2025/26",
                               study_key="DEMO-STUDY", regulations_key="DEMO-PO", **kwargs)


def test_same_target_across_weeks_fetched_once_and_room_link_ignored(client):
    session, calls = client
    refs = collect_course_references(session, (doc(block()), doc(block())))
    assert len(refs) == 1
    assert refs[0].block_count == 2
    assert "example.invalid" not in repr(refs)
    assert "Fiktive Veranstaltung" not in repr(refs)
    result = sample(session, refs)
    assert len(calls) == 1
    assert calls[0].endswith("/detail")
    assert result.details[0].series_count == 2
    assert result.details[0].status == "preview"
    assert "source_context_requires_verification" in result.details[0].preview.review_reasons
    assert not result.complete


def test_same_title_different_urls_not_merged_and_sample_limit_visible(client):
    session, calls = client
    refs = collect_course_references(session, (doc(block("/one") + block("/two")),))
    result = sample(session, refs, limit=1)
    assert result.reference_count == 2
    assert result.unchecked_count == 1
    assert len(calls) == 1


@pytest.mark.parametrize("markup", [
    "<h1>Fehler</h1>",
    block() + '<input type="password">',
    block().replace('href="/detail"', 'href="https://other.invalid/"'),
    block().replace('href="/detail"', 'onclick="script()" href="/detail"'),
    block().replace("</a></td>", '</a><a href="/other">Fiktiv</a></td>', 1),
    block().replace("<tr><td>Fiktive Angabe</td></tr>", "", 1),
    block() + block(title="Widerspruch"),
    '<td class="plan5a"><a href="/detail">Fiktiv</a></td>',
])
def test_unreliable_reference_collection_rejected_without_fetch(client, markup):
    session, calls = client
    with pytest.raises(DetailImportError):
        collect_course_references(session, (doc(markup),))
    assert not calls


@pytest.mark.parametrize("limit", [0, 11, True, "2"])
def test_invalid_limit_never_fetches(client, limit):
    session, calls = client
    refs = collect_course_references(session, (doc(block()),))
    with pytest.raises(DetailImportError):
        sample(session, refs, limit=limit)
    assert not calls


def test_duplicate_batch_rejected(client):
    session, calls = client
    refs = collect_course_references(session, (doc(block()),))
    with pytest.raises(DetailImportError):
        sample(session, refs + refs)
    assert not calls


def test_second_detail_failure_never_returns_partial_sample(client, monkeypatch):
    session, calls = client
    refs = collect_course_references(session, (doc(block("/one") + block("/two")),))
    original = session.fetch
    def fetch(url):
        if url.endswith("/two"):
            raise SourceFetchError("VERTRAULICHER_TESTWERT")
        return original(url)
    monkeypatch.setattr(session, "fetch", fetch)
    with pytest.raises(DetailImportError) as error:
        sample(session, refs)
    assert len(calls) == 1
    assert "VERTRAULICHER_TESTWERT" not in str(error.value)


def test_wrong_semester_aborts_sample(client):
    session, _ = client
    refs = collect_course_references(session, (doc(block()),))
    with pytest.raises(DetailImportError):
        fetch_detail_sample(session, refs, semester="Anderes Semester", study_key="DEMO", regulations_key="DEMO")


def test_unknown_recurrence_reports_review_without_calendar(client, monkeypatch):
    session, _ = client
    refs = collect_course_references(session, (doc(block()),))
    original = session.fetch
    def fetch(url):
        response = original(url)
        return SourceDocument(response.html.replace("woch", "UNGEPRUEFT"), url)
    monkeypatch.setattr(session, "fetch", fetch)
    result = sample(session, refs)
    assert result.details[0].status == "normalization_requires_review"
    assert result.details[0].preview is None
    assert not result.complete


def test_cli_invalid_context_never_starts_navigation(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Ungültige Eingaben dürfen keinen Abruf auslösen.")
    monkeypatch.setattr("backend.cli.search_study", forbidden)
    app = create_app({"TESTING": True})
    result = app.test_cli_runner().invoke(args=[
        "source-details-check", "--query", "DEMO", "--title", "DEMO",
        "--semester", "DEMO", "--study-key", "nicht erlaubt", "--regulations-key", "DEMO",
        "--week", "2026-W44",
    ])
    assert result.exit_code == 1


def test_cli_sample_summary_has_no_source_data(monkeypatch):
    plan = doc(block() + block())
    for name in ("search_study", "follow_named_result", "submit_labeled_search"):
        monkeypatch.setattr(f"backend.cli.{name}", lambda *args, **kwargs: plan)
    menu = SimpleNamespace(
        choices=[SimpleNamespace(key=(2026, 44), value="DEMO")], field_name="DEMO",
        button=("DEMO", "anzeigen"), form=SimpleNamespace(submit=lambda *args, **kwargs: plan),
    )
    monkeypatch.setattr("backend.cli.read_week_menu", lambda document: menu)
    monkeypatch.setattr("backend.cli.inspect_week", lambda *args: SimpleNamespace(status="ok"))
    detail = (Path(__file__).parent / "fixtures/course_detail.html").read_text(encoding="utf-8")
    monkeypatch.setattr(SourceClient, "fetch", lambda self, url: SourceDocument(detail, url))
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/start"})
    result = app.test_cli_runner().invoke(args=[
        "source-details-check", "--query", "DEMO", "--title", "DEMO",
        "--semester", "WiSe 2025/26", "--study-key", "DEMO", "--regulations-key", "DEMO",
        "--week", "2026-W44",
    ])
    assert result.exit_code == 0
    assert "Veranstaltungsblöcke: 2; eindeutige Detailziele: 1" in result.output
    assert "Nur Stichprobe" in result.output
    assert "example.invalid" not in result.output
    assert "Fiktive" not in result.output
