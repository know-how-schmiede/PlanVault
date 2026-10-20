from datetime import date, datetime, timedelta
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from backend import create_app
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.run import ImportCheckInputError, run_import_check
from version import __version__


START, END = date(2026, 12, 28), date(2027, 1, 10)


def plan(index=0, notice="", target="/detail"):
    options = []
    for i in range(2):
        day = START + timedelta(days=7 * i)
        options.append(f'<option value="demo-{i}" {"selected" if i == index else ""}>'
                       f'Woche: {day.isocalendar().week} {day:%d.%m.%Y} ---- {day+timedelta(days=6):%d.%m.%Y}</option>')
    headings = "".join(f"<th>{name} {START+timedelta(days=7*index+i):%d.%m.%Y}{notice}</th>"
                       for i, name in enumerate(("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag")))
    block = (f'<table><tr><td class="plan5a"><a href="{target}">FIKTIVER-TITEL</a></td></tr>' +
             "<tr><td>DEMO</td></tr>" * 7 + "</table>")
    return ('<form action="/week" method="post"><select name="demo-week">' + "".join(options) +
            '</select><input type="submit" name="go" value="anzeigen"></form>' +
            f"<table><tr>{headings}</tr></table>" + block)


@pytest.fixture
def workflow(monkeypatch):
    entry = ('<form action="/search"><label for="study">Studiengang</label>'
             '<input id="study" name="query"><input type="submit" name="find" value="Auswahl"></form>')
    selected = ('<form action="/plan"><label for="study">Studiengang</label>'
                '<input id="study" readonly><input name="selected" type="hidden" value="DEMO">'
                '<input type="submit" name="go" value="Suche starten"></form>')
    detail = (Path(__file__).parent / "fixtures/course_detail.html").read_text(encoding="utf-8")
    state = {"calls": [], "notice": "", "fail": None, "second_target": "/detail"}

    def fetch(self, url=None, **kwargs):
        path = urlsplit(url or "https://example.invalid/start").path
        state["calls"].append(path)
        if state["fail"] == path:
            raise SourceFetchError("VERTRAULICHER-TESTWERT")
        if path == "/start":
            html = entry
        elif path == "/search":
            html = '<a href="/selected">Fiktives Studium</a>'
        elif path == "/selected":
            html = selected
        elif path == "/plan":
            html = plan()
        elif path == "/week":
            index = int(dict(kwargs["form"])["demo-week"].removeprefix("demo-"))
            html = plan(index, state["notice"], state["second_target"] if index else "/detail")
        elif path in {"/detail", "/second"}:
            html = detail
        else:
            pytest.fail("Unerwarteter Abruf.")
        return SourceDocument(html, url or "https://example.invalid/start")

    monkeypatch.setattr(SourceClient, "fetch", fetch)
    return state


def run(**kwargs):
    arguments = dict(query="Fiktiv", title="Fiktives Studium", semester="WiSe 2025/26",
                     study_key="DEMO", regulations_key="DEMO-PO", start=START, end=END,
                     requested=((2026, 53), (2027, 1)))
    arguments.update(kwargs)
    with SourceClient("https://example.invalid/start") as client:
        return run_import_check(client, **arguments)


def test_combined_run_deduplicates_across_weeks_and_never_publishes(workflow):
    report = run()
    assert report.status == "needs_review"
    assert report.stage == "finished"
    assert report.missing_weeks == ()
    assert report.checked_details == report.reference_count == 1
    assert report.unchecked_details == 0
    assert workflow["calls"].count("/detail") == 1
    assert len(report.checked_weeks) == 2
    assert not report.complete and not report.published
    assert "source_identity_unverified" in report.blockers
    assert "semester_content_unverified" in report.blockers
    assert datetime.fromisoformat(report.finished_at) >= datetime.fromisoformat(report.started_at)


def test_report_contains_only_allowlisted_metadata(workflow):
    report = run()
    text = report.to_json()
    for forbidden in ("example.invalid", "FIKTIVER-TITEL", "DEMO", "Fiktives", "WiSe", "/detail"):
        assert forbidden not in text
    assert json.loads(text)["app_version"] == __version__
    assert json.loads(text)["published"] is False


def test_missing_week_and_limited_details_are_explicit(workflow):
    report = run(requested=((2026, 53),))
    assert report.missing_weeks == ((2027, 1),)
    assert report.checked_details == 1
    assert "missing_weeks" in report.blockers
    workflow["second_target"] = "/second"
    report = run(detail_limit=1)
    assert report.reference_count == 2
    assert report.unchecked_details == 1
    assert "unchecked_details" in report.blockers


def test_holiday_view_blocks_all_details(workflow):
    workflow["notice"] = " Fiktive Ferien"
    report = run()
    assert report.stage == "weeks"
    assert report.status == "needs_review"
    assert report.checked_details == 0
    assert report.failed_weeks == ((2026, 53),)
    assert "/detail" not in workflow["calls"]


@pytest.mark.parametrize("path,stage", [("/search", "navigation"), ("/week", "weeks"), ("/detail", "details")])
def test_failures_become_sanitized_reports(workflow, path, stage):
    workflow["fail"] = path
    report = run()
    assert report.status == "failed"
    assert report.stage == stage
    assert report.checked_details == 0
    assert not report.published
    assert "VERTRAULICHER" not in report.to_json()


@pytest.mark.parametrize("kwargs", [
    {"requested": ((2026, 53), (2026, 53))}, {"requested": ((2027, 54),)},
    {"requested": ((2027, 4),)}, {"start": END, "end": START},
])
def test_invalid_request_fails_before_network(workflow, kwargs):
    with pytest.raises(ImportCheckInputError):
        run(**kwargs)
    assert workflow["calls"] == []


def test_cli_json_remains_parseable_with_nonzero_exit(workflow):
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/start"})
    result = app.test_cli_runner().invoke(args=[
        "source-import-check", "--query", "Fiktiv", "--title", "Fiktives Studium",
        "--semester", "WiSe 2025/26", "--study-key", "DEMO", "--regulations-key", "DEMO-PO",
        "--start", "2026-12-28", "--end", "2027-01-10", "--week", "2026-W53", "--json",
    ])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report["checked_details"] == 1
    assert report["missing_weeks"] == [[2027, 1]]
    assert "example.invalid" not in result.output
