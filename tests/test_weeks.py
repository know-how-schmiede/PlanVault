from datetime import date, timedelta

import pytest

from backend import create_app
from backend.importer.forms import FormNavigationError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.weeks import read_week_menu, inspect_week, audit_weeks


START = date(2026, 12, 28)
END = date(2027, 1, 10)
DAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag")


def html(*, selected=0, blocks=True, notice="", shifted=False):
    options = []
    for index, monday in enumerate((START, START + timedelta(days=7))):
        sunday = monday + timedelta(days=6)
        options.append(f'<option value="demo-{index}" {"selected" if selected == index else ""}>'
                       f'Woche: {monday.isocalendar().week} {monday:%d.%m.%Y} ---- {sunday:%d.%m.%Y}</option>')
    day = START + timedelta(days=7 * selected + (7 if shifted else 0))
    headers = "".join(f"<th>{name} {day + timedelta(days=i):%d.%m.%Y}{notice}</th>" for i, name in enumerate(DAYS))
    return ('<form action="/week" method="post"><select name="demo-week">' + "".join(options) +
            '</select><input type="submit" name="demo-show" value="anzeigen"></form>'
            f'<table><tr>{headers}</tr><tr>' +
            ('<td class="plan5a">Fiktive Veranstaltung</td>' if blocks else '<td>Keine erkannten Blöcke</td>') +
            "</tr></table>")


def doc(markup=None):
    return SourceDocument(html() if markup is None else markup, "https://example.invalid/plan")


@pytest.fixture
def client(monkeypatch):
    with SourceClient("https://example.invalid/plan") as client:
        calls = []
        def fetch(link=None, **kwargs):
            calls.append(kwargs)
            selected = int(dict(kwargs["form"])["demo-week"].removeprefix("demo-"))
            return doc(html(selected=selected))
        monkeypatch.setattr(client, "fetch", fetch)
        yield client, calls


def test_date_range_determines_iso_year_and_private_values_are_hidden():
    menu = read_week_menu(doc())
    assert [choice.key for choice in menu.choices] == [(2026, 53), (2027, 1)]
    assert menu.selected == (2026, 53)
    assert "demo-week" not in repr(menu)
    assert "example.invalid" not in repr(menu)
    assert "demo-0" not in repr(menu)


def test_requested_weeks_checked_against_independent_period(client):
    session, calls = client
    audit = audit_weeks(session, doc(), start=START, end=END, requested=((2026, 53), (2027, 1)))
    assert audit.coverage.weeks_complete
    assert not audit.complete
    assert len(calls) == 2
    assert all(result.status == "ok" for result in audit.results)


def test_offered_but_unvisited_week_remains_missing(client):
    session, _ = client
    audit = audit_weeks(session, doc(), start=START, end=END, requested=((2026, 53),))
    assert audit.coverage.missing == ((2027, 1),)
    assert not audit.coverage.weeks_complete


@pytest.mark.parametrize("markup", [
    lambda: html().replace("Woche: 53", "Woche: 52"),
    lambda: html().replace("28.12.2026 ----", "29.12.2026 ----"),
    lambda: html().replace("03.01.2027</option>", "04.01.2027</option>"),
    lambda: html().replace("28.12.2026 ----", "31.02.2026 ----"),
    lambda: html().replace('value="demo-1"', 'value="demo-0"'),
    lambda: html().replace('value="demo-1"', 'selected value="demo-1"'),
    lambda: html().replace('name="demo-week"', 'name="demo-week" multiple'),
    lambda: html().replace("anzeigen", "Andere Aktion"),
    lambda: "<h1>Fehler</h1>",
    lambda: html() + '<input type="password">',
])
def test_invalid_week_menu_is_rejected(markup):
    with pytest.raises(FormNavigationError):
        read_week_menu(doc(markup()))


def test_stale_selected_week_rejected():
    expected = read_week_menu(doc()).choices[1]
    with pytest.raises(FormNavigationError):
        inspect_week(doc(), expected)


def test_correct_selected_week_but_wrong_headers_rejected():
    expected = read_week_menu(doc()).choices[0]
    with pytest.raises(FormNavigationError):
        inspect_week(doc(html(shifted=True)), expected)


@pytest.mark.parametrize("blocks,notice,status", [
    (False, "", "empty_unverified"),
    (False, " Fiktive Ferien", "notes_require_review"),
    (True, " Fiktiver Hinweis", "notes_require_review"),
])
def test_empty_and_holiday_views_are_not_confirmed_complete(blocks, notice, status):
    expected = read_week_menu(doc()).choices[0]
    result = inspect_week(doc(html(blocks=blocks, notice=notice)), expected)
    assert result.status == status


def test_network_failure_stops_and_marks_remaining_missing(client, monkeypatch):
    session, _ = client
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise SourceFetchError("Bereinigter Testfehler.")
    monkeypatch.setattr(session, "fetch", fail)
    audit = audit_weeks(session, doc(), start=START, end=END, requested=((2026, 53), (2027, 1)))
    assert len(calls) == 1
    assert audit.coverage.failed == ((2026, 53),)
    assert audit.coverage.missing == ((2027, 1),)


def test_menu_change_in_last_response_fails(client, monkeypatch):
    session, _ = client
    changed = html().replace("Woche: 1 04.01.2027 ---- 10.01.2027", "Woche: 2 11.01.2027 ---- 17.01.2027")
    monkeypatch.setattr(session, "fetch", lambda *args, **kwargs: doc(changed))
    audit = audit_weeks(session, doc(), start=START, end=END, requested=((2026, 53),))
    assert audit.coverage.failed == ((2026, 53),)


@pytest.mark.parametrize("requested", [(), ((2026, 53), (2026, 53)), ((2027, 5),)])
def test_invalid_request_does_not_fetch(client, requested):
    session, calls = client
    with pytest.raises(FormNavigationError):
        audit_weeks(session, doc(), start=START, end=END, requested=requested)
    assert not calls


def test_cli_partial_selection_reports_missing(monkeypatch):
    monkeypatch.setattr("backend.cli.search_study", lambda *args: doc())
    monkeypatch.setattr("backend.cli.follow_named_result", lambda *args, **kwargs: doc())
    monkeypatch.setattr("backend.cli.submit_labeled_search", lambda *args, **kwargs: doc())
    monkeypatch.setattr(SourceClient, "fetch", lambda *args, **kwargs: doc())
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/plan"})
    result = app.test_cli_runner().invoke(args=[
        "source-weeks-check", "--query", "Fiktiv", "--title", "Fiktiv",
        "--start", "2026-12-28", "--end", "2027-01-10", "--week", "2026-W53",
    ])
    assert result.exit_code == 1
    assert "Fehlende Wochen: 1" in result.output
    assert "Kein Semesterimport" in result.output
    assert "example.invalid" not in result.output
