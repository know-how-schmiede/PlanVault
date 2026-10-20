from urllib.parse import parse_qsl, urlsplit

import pytest

from backend.importer.forms import FormNavigationError, read_search_form
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError


HTML = """<form action="../search?discard=old" method="get">
<input name="token" type="hidden" value="DEMO-SECRET">
<input name="term" value="">
<select name="semester"><option value="a">DEMO A</option><option value="b" selected>DEMO B</option></select>
<input name="flag" type="checkbox" checked value="x">
<input name="flag" type="checkbox" value="y">
<input name="ignored" disabled value="private">
<button name="search" value="yes">Suchen</button>
<button name="search" value="other">Andere Suche</button></form>"""


def read(html=HTML):
    return read_search_form(SourceDocument(html, "https://example.invalid/folder/page"),
                            required_fields={"term", "semester"})


@pytest.fixture
def client(monkeypatch):
    client = SourceClient("https://example.invalid/start")
    calls = []
    def fetch(link=None, **kwargs):
        calls.append((link, kwargs))
        return SourceDocument("<html>DEMO</html>", link)
    monkeypatch.setattr(client, "fetch", fetch)
    yield client, calls
    client.close()


def test_get_uses_observed_action_defaults_and_explicit_button(client):
    session, calls = client
    form = read()
    form.submit(session, values={"term": ("Fiktive Suche ä",), "semester": ("a",)}, button=("search", "yes"))
    url, kwargs = calls[0]
    assert urlsplit(url).path == "/search"
    assert parse_qsl(urlsplit(url).query) == [
        ("token", "DEMO-SECRET"), ("term", "Fiktive Suche ä"), ("semester", "a"),
        ("flag", "x"), ("search", "yes"),
    ]
    assert kwargs == {}
    assert "DEMO-SECRET" not in repr(form)
    assert "example.invalid" not in repr(form)


def test_post_keeps_action_query_and_repeated_hidden_fields(client):
    session, calls = client
    form = read(HTML.replace('method="get"', 'method="post"').replace(
        '<input name="term"', '<input type="hidden" name="token" value="SECOND"><input name="term"'))
    form.submit(session, button=("search", "yes"))
    url, kwargs = calls[0]
    assert url.endswith("/search?discard=old")
    assert [value for name, value in kwargs["form"] if name == "token"] == ["DEMO-SECRET", "SECOND"]


@pytest.mark.parametrize("values", [
    {"token": ("changed",)}, {"unknown": ("x",)}, {"semester": ("not-offered",)},
    {"semester": ("a", "b")}, {"term": "wrong-type"},
])
def test_invalid_overrides_never_send_request(client, values):
    session, calls = client
    with pytest.raises(FormNavigationError):
        read().submit(session, values=values, button=("search", "yes"))
    assert calls == []


@pytest.mark.parametrize("button", [None, ("search", "unknown")])
def test_submit_button_must_be_explicit_and_observed(client, button):
    session, calls = client
    with pytest.raises(FormNavigationError):
        read().submit(session, button=button)
    assert calls == []


@pytest.mark.parametrize("html", [
    HTML + HTML, "<html>Fehler</html>", HTML + '<input type="password">',
    HTML.replace('method="get"', 'method="delete"'),
    HTML.replace('method="get"', 'method="post" enctype="multipart/form-data"'),
    '<base href="https://example.invalid/">' + HTML,
    HTML.replace('<input name="term"', '<input form="outside" name="term"'),
    HTML.replace('<input name="term"', '<input type="file" name="term"'),
    HTML.replace('<input name="term"', '<input onchange="script()" name="term"'),
    HTML.replace("<form ", '<form onsubmit="script()" '),
    HTML.replace('value="a"', 'value="b"'),
])
def test_unknown_or_ambiguous_forms_rejected(html):
    with pytest.raises(FormNavigationError) as error:
        read(html)
    assert "DEMO-SECRET" not in str(error.value)


def test_external_action_rejected_before_submission(client):
    session, calls = client
    form = read(HTML.replace("../search?discard=old", "https://elsewhere.invalid/"))
    with pytest.raises(SourceFetchError):
        form.submit(session, button=("search", "yes"))
    assert calls == []


def test_multi_select_and_textarea(client):
    session, calls = client
    html = HTML.replace('<select name="semester">', '<select name="semester" multiple>')
    html = html.replace("</form>", '<textarea name="note">Line1\nLine2</textarea></form>')
    read(html).submit(session, values={"semester": ("a", "b")}, button=("search", "yes"))
    pairs = parse_qsl(urlsplit(calls[0][0]).query)
    assert [v for k, v in pairs if k == "semester"] == ["a", "b"]
    assert ("note", "Line1\r\nLine2") in pairs


def test_duplicate_editable_names_are_not_guessed(client):
    session, calls = client
    form = read(HTML.replace("</form>", '<input name="term"></form>'))
    with pytest.raises(FormNavigationError):
        form.submit(session, values={"term": ("new",)}, button=("search", "yes"))
    assert not calls
