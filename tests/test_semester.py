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
    assert report["schema_version"] == 5
    assert report["weekday_coverage"]["unobserved_weekdays"] == list(range(7))
    assert report["weekday_coverage"]["blocked_details"] is None
    assert not report["weekday_coverage"]["weekend_coverage_verified"]
    if not fail:
        assert all(v["block_count"] == 1 and v["visible_weekdays"] == [] for v in report["views"])
    assert not report["complete"] and not report["published"]
    for secret in ("example.invalid", "PRIVATE-NAMESPACE", "Fiktiver", "VERTRAULICH", "record"):
        assert secret not in result.output

@pytest.mark.parametrize("days", [("Montag", "Freitag"), ("Montag", "Samstag", "Sonntag"), ()])
def test_alternative_blocks_are_not_empty_and_weekdays_are_only_observed(session, monkeypatch, days):
    client, _ = session
    def fetch(*args, **kwargs):
        selected = dict(kwargs["form"])["demo-view"]
        headers = "<table><tr>" + "".join(f"<th>{day}</th>" for day in days) + "</tr></table>"
        response = document(selected, (1,), headers)
        return SourceDocument(response.html.replace('class="plan5a"', 'class="plan5"'), response.location)
    monkeypatch.setattr(client, "fetch", fetch)
    results = audit_semester_views(client, document(), identity_policy=SourceIdentityPolicy("record", "demo"))
    expected = tuple(("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag").index(d) for d in days)
    assert all(v.status == "observed" and v.reference_count == 1 for v in results)
    assert all(v.visible_weekdays == expected for v in results)
@pytest.mark.parametrize("visible", [(), (0, 1, 2, 3, 4), tuple(range(7))])
def test_weekday_headers_never_prove_weekend_completeness(visible):
    from backend.importer.semester import SemesterViewResult, weekday_coverage
    views = (SemesterViewResult("semester", "observed", 0, 0, (), visible),)
    result = weekday_coverage(views)
    assert result["unobserved_weekdays"] == sorted(set(range(7)) - set(visible))
    assert result["blocked_details"] is None
    assert not result["details_checked"]
    assert not result["weekend_coverage_verified"]


def test_weekday_audit_uses_local_date_and_preserves_blocked_details():
    from backend.importer.semester import SemesterViewResult, weekday_coverage
    from backend.importer.details import DetailResult, DetailSample
    from backend.parser.normalize import CalendarPreview, Occurrence
    # Sunday locally, Saturday in UTC: count by the source's local calendar date.
    event = Occurrence("demo", 0, "2026-10-24T22:15:00+00:00", "2026-10-24T22:45:00+00:00",
                       "2026-10-25", 2026, 43, None, None)
    preview = CalendarPreview("demo", "Fiktiv", "Demo", (event,), ())
    sample = DetailSample(2, 2, (DetailResult("demo", 1, "preview", preview),
                                DetailResult("blocked", 1, "needs_review", None)))
    views = (SemesterViewResult("semester", "observed", 2, 0, (), (0, 1, 2, 3, 4)),)
    result = weekday_coverage(views, sample)
    assert result["occurrences_by_weekday"] == [0, 0, 0, 0, 0, 0, 1]
    assert result["occurrence_weekdays_outside_views"] == [6]
    assert result["blocked_details"] == 1
    assert result["details_checked"]
    assert not result["weekend_coverage_verified"]
    assert "Fiktiv" not in json.dumps(result)


def test_partial_detail_sample_cannot_claim_all_details_checked():
    from backend.importer.semester import weekday_coverage
    from backend.importer.details import DetailSample
    result = weekday_coverage((), DetailSample(2, 2, ()))
    assert not result["details_checked"]
    assert result["occurrences_by_weekday"] == [0] * 7
    assert not result["weekend_coverage_verified"]
