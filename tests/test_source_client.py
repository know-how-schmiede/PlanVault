from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from backend import create_app
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError, _Redirects
from backend.importer.service import fetch_course_preview
from backend.parser import CourseContext, SourceParseError


BASE = "https://example.invalid/start"


class Response(BytesIO):
    def __init__(self, body=b"<html>DEMO</html>", *, mime="text/html; charset=utf-8", status=200):
        super().__init__(body)
        self.headers = Message()
        self.headers["Content-Type"] = mime
        self.status = status

    def geturl(self):
        return BASE


class FakeOpener:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("backend.importer.http.time.sleep", lambda _: None)
    with SourceClient(BASE) as client:
        yield client


@pytest.mark.parametrize("url", ["", "http://example.invalid", "https://user:secret@example.invalid",
                                "https://example.invalid/#fragment", "https://example.invalid:bad",
                                "https://example.invalid/\nprivate", "https://example.invalid/ä"])
def test_invalid_base_is_rejected_without_echoing_input(url):
    with pytest.raises(SourceFetchError) as error:
        SourceClient(url)
    assert "example.invalid" not in str(error.value)
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("link", ["https://elsewhere.invalid/", "//elsewhere.invalid/",
                                 "http://example.invalid/", "https://example.invalid:444/",
                                 "https://user@example.invalid/", "javascript:alert(1)"])
def test_foreign_or_unsafe_navigation_is_rejected(client, link):
    with pytest.raises(SourceFetchError):
        client.resolve(link)


def test_relative_link_resolves_against_current_page(client):
    assert client.resolve("detail", relative_to="https://example.invalid/folder/page") == \
        "https://example.invalid/folder/detail"


def test_get_preserves_memory_only_document_and_timeout(client):
    opener = FakeOpener([Response()])
    client._opener = opener
    document = client.fetch()
    assert document.html == "<html>DEMO</html>"
    assert "example.invalid" not in repr(document)
    assert "DEMO" not in repr(document)
    assert opener.requests[0][1] == 10
    assert opener.requests[0][0].get_method() == "GET"


def test_post_preserves_repeated_form_fields_and_is_not_retried(client):
    opener = FakeOpener([URLError("SECRET https://example.invalid/private")])
    client._opener = opener
    with pytest.raises(SourceFetchError) as error:
        client.fetch("/search", form=[("choice", "A"), ("choice", "B")])
    assert len(opener.requests) == 1
    assert opener.requests[0][0].data == b"choice=A&choice=B"
    assert "SECRET" not in str(error.value)


def test_temporary_get_failure_retries_with_bounded_backoff(client, monkeypatch):
    sleeps = []
    monkeypatch.setattr("backend.importer.http.time.sleep", sleeps.append)
    client._opener = FakeOpener([URLError("secret"), Response()])
    client.fetch()
    assert len(client._opener.requests) == 2
    assert 1 in sleeps


@pytest.mark.parametrize("status, count", [(403, 1), (404, 1), (429, 3), (503, 3)])
def test_retry_status_policy_and_sanitized_errors(client, status, count):
    client._opener = FakeOpener([
        HTTPError(BASE, status, "SECRET", {}, BytesIO(b"SECRET")) for _ in range(count)
    ])
    with pytest.raises(SourceFetchError) as error:
        client.fetch()
    assert len(client._opener.requests) == count
    assert "SECRET" not in str(error.value)
    assert "example.invalid" not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize("response", [
    lambda: Response(b""),
    lambda: Response(b"{}", mime="application/json"),
    lambda: Response(b"\xff", mime="text/html; charset=utf-8"),
    lambda: Response(b"abc", mime="text/html; charset=unknown-encoding"),
    lambda: Response(status=204),
])
def test_invalid_responses_do_not_produce_documents(client, response):
    client._opener = FakeOpener([response()])
    with pytest.raises(SourceFetchError):
        client.fetch()


def test_oversized_document_is_rejected(client):
    client.max_bytes = 5
    client._opener = FakeOpener([Response(b"123456")])
    with pytest.raises(SourceFetchError):
        client.fetch()


def test_compressed_response_is_rejected(client):
    response = Response()
    response.headers["Content-Encoding"] = "gzip"
    client._opener = FakeOpener([response])
    with pytest.raises(SourceFetchError):
        client.fetch()


def test_limit_and_closed_session_prevent_network_access(client):
    client.max_requests = 1
    client._opener = FakeOpener([Response()])
    client.fetch()
    with pytest.raises(SourceFetchError):
        client.fetch()
    client.close()
    with pytest.raises(SourceFetchError):
        client.fetch()
    assert len(client._opener.requests) == 1


def test_redirect_is_checked_before_following_and_counts_toward_budget(client):
    handler = _Redirects(client)
    req = Request(BASE)
    with pytest.raises(SourceFetchError):
        handler.redirect_request(req, None, 302, "", {}, "https://elsewhere.invalid/")
    assert client._count == 0
    redirected = handler.redirect_request(req, None, 302, "", {}, "https://example.invalid/next")
    assert redirected.full_url == "https://example.invalid/next"
    assert client._count == 1
    with pytest.raises(SourceFetchError):
        handler.redirect_request(Request(BASE, data=b"a=b"), None, 302, "", {}, BASE)


def test_fetch_parse_normalize_integration(client):
    html = (Path(__file__).parent / "fixtures/course_detail.html").read_bytes()
    client._opener = FakeOpener([Response(html)])
    result = fetch_course_preview(client, "/detail", CourseContext("DEMO", "DEMO-STUDY", "DEMO-PO", "WiSe 2025/26"))
    assert result.title == "Fiktives Labor Datenanalyse"
    assert len(result.occurrences) > 0
    assert not result.complete


def test_login_page_is_not_an_empty_course(client):
    client._opener = FakeOpener([Response(b'<input type="password">')])
    with pytest.raises(SourceParseError):
        fetch_course_preview(client, "/detail", CourseContext("DEMO", "DEMO-STUDY", "DEMO-PO", "WiSe 2025/26"))


@pytest.mark.parametrize("html, exit_code", [
    ("<form><select><option>DEMO</option></select></form>", 0),
    ('<form><input type="password"><select></select></form>', 1),
    ("<h1>Fehler</h1>", 1),
])
def test_source_check_cli_does_not_expose_document_or_address(monkeypatch, html, exit_code):
    monkeypatch.setattr(SourceClient, "fetch", lambda self: SourceDocument(html, BASE))
    app = create_app({"TESTING": True, "LSF_BASE_URL": BASE})
    result = app.test_cli_runner().invoke(args=["source-check"])
    assert result.exit_code == exit_code
    assert "example.invalid" not in result.output
    assert "DEMO" not in result.output
    if exit_code == 0:
        assert "Kein Import" in result.output


def test_source_check_missing_config_is_clear_error():
    app = create_app({"TESTING": True, "LSF_BASE_URL": ""})
    result = app.test_cli_runner().invoke(args=["source-check"])
    assert result.exit_code == 1
    assert "Quellkonfiguration" in result.output


def test_web_request_never_calls_source(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Webseitenaufruf darf keinen Quellabruf starten.")
    monkeypatch.setattr(SourceClient, "fetch", forbidden)
    app = create_app({"TESTING": True, "LSF_BASE_URL": BASE})
    assert app.test_client().get("/").status_code == 200
