import json

import pytest

from backend import create_app
from backend.importer.forms import FormNavigationError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.identity import SourceIdentityPolicy
from backend.importer.semester import audit_semester_views


def document(selected="week", records=(1,), suffix=""):
    options = [("week", "Woche: 43 19.10.2026 ---- 25.10.2026"),
               ("all", "Semesteransicht"), ("special", "Semesterzeitansicht nur Block/Einzeltermine")]
    html = '<form action="/view" method="post"><select name="demo-view">'
    html += "".join(f'<option value="{key}" {"selected" if selected == key else ""}>{label}</option>'
                    for key, label in options)
    html += '</select><input type="submit" name="show" value="anzeigen"></form>'
    for record in records:
        html += (f'<table><tr><td class="plan5a"><a href="/detail?record={record}">'
                 f'Fiktiver Kurs {record}</a></td></tr>' + "<tr><td>DEMO</td></tr>" * 7 + "</table>")
    return SourceDocument(html + suffix, "https://example.invalid/view")


@pytest.fixture
def session(monkeypatch):
    with SourceClient("https://example.invalid/start") as client:
        calls = []
        def fetch(*args, **kwargs):
            selected = dict(kwargs["form"])["demo-view"]
            calls.append(selected)
            return document(selected, (1, 2) if selected == "all" else (2, 3))
        monkeypatch.setattr(client, "fetch", fetch)
        yield client, calls


def test_two_views_preserve_additional_special_targets(session):
    client, calls = session
    views = audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))
    assert calls == ["all", "special"]
    assert [v.reference_count for v in views] == [2, 2]
    assert views[1].additional_count == 1
    assert "example.invalid" not in repr(views)
    assert "Fiktiver" not in repr(views)


def test_empty_view_is_not_confirmed(session, monkeypatch):
    client, _ = session
    monkeypatch.setattr(client, "fetch", lambda *args, **kw: document(dict(kw["form"])["demo-view"], ()))
    views = audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))
    assert all(v.status == "empty_unverified" for v in views)


@pytest.mark.parametrize("change", [
    lambda d: document("week"),
    lambda d: SourceDocument(d.html.replace("Woche: 43 19.10.2026 ---- 25.10.2026",
                                          "Woche: 44 26.10.2026 ---- 01.11.2026"), d.location),
    lambda d: SourceDocument(d.html + '<input type="password">', d.location),
])
def test_stale_or_changed_or_login_response_rejected(session, monkeypatch, change):
    client, _ = session
    monkeypatch.setattr(client, "fetch", lambda *args, **kw: change(document("all")))
    with pytest.raises(FormNavigationError):
        audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))


@pytest.mark.parametrize("replacement", [
    'value="all" disabled', 'value="special"', 'value=""',
])
def test_invalid_view_option_does_not_fetch(session, replacement):
    client, calls = session
    initial = document()
    initial = SourceDocument(initial.html.replace('value="all"', replacement), initial.location)
    with pytest.raises(FormNavigationError):
        audit_semester_views(client, initial, identity_policy=SourceIdentityPolicy("record", "demo"))
    assert calls == []


def test_missing_policy_rejected_without_request(session):
    client, calls = session
    with pytest.raises(FormNavigationError):
        audit_semester_views(client, document(), identity_policy=None)
    assert calls == []


def test_second_view_failure_returns_no_partial_result(session, monkeypatch):
    client, _ = session
    def fetch(*args, **kwargs):
        selected = dict(kwargs["form"])["demo-view"]
        if selected == "special":
            raise SourceFetchError("Bereinigter Testfehler.")
        return document(selected)
    monkeypatch.setattr(client, "fetch", fetch)
    with pytest.raises(SourceFetchError):
        audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))


def test_cli_missing_configuration_fails_before_navigation(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Ohne Kennung darf kein Abruf erfolgen.")
    monkeypatch.setattr("backend.cli.search_study", forbidden)
    app = create_app({"TESTING": True, "LSF_ID_PARAMETER": "", "LSF_ID_NAMESPACE": ""})
    result = app.test_cli_runner().invoke(args=["source-semester-check", "--query", "Demo", "--title", "Demo"])
    assert result.exit_code == 1
    assert "konfigurierte Quellkennung" in result.output


def test_second_view_failure_returns_no_partial_result(session, monkeypatch):
    client, _ = session
    def fetch(*args, **kwargs):
        selected = dict(kwargs["form"])["demo-view"]
        if selected == "special":
            raise SourceFetchError("Bereinigter Testfehler.")
        return document(selected)
    monkeypatch.setattr(client, "fetch", fetch)
    with pytest.raises(SourceFetchError):
        audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))


def test_cli_missing_configuration_fails_before_navigation(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Ohne Kennung darf kein Abruf erfolgen.")
    monkeypatch.setattr("backend.cli.search_study", forbidden)
    app = create_app({"TESTING": True, "LSF_ID_PARAMETER": "", "LSF_ID_NAMESPACE": ""})
    result = app.test_cli_runner().invoke(args=["source-semester-check", "--query", "Demo", "--title", "Demo"])
    assert result.exit_code == 1
    assert "konfigurierte Quellkennung" in result.output


@pytest.mark.parametrize("fail", [False, True])
def test_cli_report_is_private_and_never_published(monkeypatch, fail):
    for name in ("search_study", "follow_named_result", "submit_labeled_search"):
        monkeypatch.setattr("backend.cli." + name, lambda *args, **kwargs: document())
    def fetch(*args, **kwargs):
        if fail:
            raise SourceFetchError("VERTRAULICH")
        return document(dict(kwargs["form"])["demo-view"])
    monkeypatch.setattr(SourceClient, "fetch", fetch)
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/start",
                      "LSF_ID_PARAMETER": "record", "LSF_ID_NAMESPACE": "PRIVATE-NAMESPACE"})
    result = app.test_cli_runner().invoke(args=["source-semester-check", "--query", "Demo",
                                              "--title", "Demo", "--json"])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report["status"] == ("failed" if fail else "needs_review")
    assert not report["complete"] and not report["published"]
    for secret in ("example.invalid", "PRIVATE-NAMESPACE", "Fiktiver", "VERTRAULICH", "record"):
        assert secret not in result.output
