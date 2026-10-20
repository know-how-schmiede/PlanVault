from urllib.parse import parse_qsl, urlsplit

import pytest

from backend import create_app
from backend.importer.forms import FormNavigationError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.navigation import search_study, follow_named_result, submit_labeled_search


ENTRY = """<form action="/search"><fieldset><legend>Suchkriterien</legend>
<input type="hidden" name="session" value="FIKTIV">
<label for="study">Studiengang</label><input id="study" name="query">
<input type="submit" name="find" value="Auswahl"></fieldset></form>"""
SELECTED = """<form action="/plan"><fieldset>
<label for="study">Studiengang</label><input id="study" readonly value="Fiktives Studium">
<input type="hidden" name="selected" value="DEMO-PO">
<input type="submit" name="go" value="Suche starten">
<input type="submit" name="go" value="Suche starten"></fieldset></form>"""
RESULTS = '<a href="/selected">Fiktives Studium  (DEMO-PO)</a>'
PLAN = '<table><tr><td class="plan5a">Fiktive Veranstaltung</td></tr></table>'


@pytest.fixture
def session(monkeypatch):
    client = SourceClient("https://example.invalid/start")
    calls = []
    responses = [ENTRY, RESULTS, SELECTED, PLAN]
    def fetch(link=None, **kwargs):
        calls.append((link, kwargs))
        return SourceDocument(responses[len(calls)-1], link or "https://example.invalid/start")
    monkeypatch.setattr(client, "fetch", fetch)
    yield client, calls
    client.close()


def test_full_navigation_keeps_selected_id_and_equivalent_submit_buttons(session):
    client, calls = session
    result = search_study(client, "Fiktiv")
    selected = follow_named_result(client, result, title="Fiktives Studium (DEMO-PO)")
    plan = submit_labeled_search(client, selected, field_label="Studiengang", button_caption="Suche starten")
    assert plan.html == PLAN
    assert len(calls) == 4
    assert ("query", "Fiktiv") in parse_qsl(urlsplit(calls[1][0]).query)
    assert parse_qsl(urlsplit(calls[3][0]).query) == [("selected", "DEMO-PO"), ("go", "Suche starten")]


@pytest.mark.parametrize("html", [
    ENTRY.replace('for="study"', 'for="missing"'),
    ENTRY.replace('id="study"', 'id="other"'),
    ENTRY.replace('<fieldset>', '<fieldset disabled>'),
    ENTRY + ENTRY,
    ENTRY.replace("Auswahl", "Andere Schaltfläche"),
    ENTRY.replace("</form>", '<input type="submit" name="other" value="Auswahl"></form>'),
])
def test_ambiguous_form_never_sends(session, html):
    client, calls = session
    with pytest.raises(FormNavigationError):
        submit_labeled_search(client, SourceDocument(html, "https://example.invalid/start"),
                              field_label="Studiengang", button_caption="Auswahl", search_text="Fiktiv")
    assert not calls


@pytest.mark.parametrize("html", [
    '<a href="/one">DEMO</a><a href="/two">DEMO</a>',
    '<a href="/one" onclick="script()">DEMO</a>',
    '<h1>Fehler</h1>',
    '<input type="password"><a href="/one">DEMO</a>',
])
def test_unreliable_result_never_followed(session, html):
    client, calls = session
    with pytest.raises(FormNavigationError):
        follow_named_result(client, SourceDocument(html, "https://example.invalid/start"), title="DEMO")
    assert not calls


def test_foreign_result_never_followed(session):
    client, calls = session
    with pytest.raises(SourceFetchError):
        follow_named_result(client, SourceDocument('<a href="https://other.invalid">DEMO</a>',
                                                   "https://example.invalid/start"), title="DEMO")
    assert not calls


def test_selected_readonly_control_cannot_be_overwritten(session):
    client, calls = session
    with pytest.raises(FormNavigationError):
        submit_labeled_search(client, SourceDocument(SELECTED, "https://example.invalid/start"),
                              field_label="Studiengang", button_caption="Suche starten", search_text="Other")
    assert not calls


@pytest.mark.parametrize("plan,code", [(PLAN, 0), ("<h1>Fehler</h1>", 1),
                                     ('<input type="password">' + PLAN, 1)])
def test_plan_check_cli(monkeypatch, plan, code):
    responses = iter([ENTRY, RESULTS, SELECTED, plan])
    monkeypatch.setattr(SourceClient, "fetch", lambda self, *args, **kwargs:
                        SourceDocument(next(responses), "https://example.invalid/page"))
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/start"})
    result = app.test_cli_runner().invoke(args=[
        "source-plan-check", "--query", "Fiktiv", "--title", "Fiktives Studium (DEMO-PO)",
    ])
    assert result.exit_code == code
    assert "example.invalid" not in result.output
    assert "FIKTIV" not in result.output
    if code == 0:
        assert "Kein Import" in result.output
