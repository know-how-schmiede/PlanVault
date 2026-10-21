from pathlib import Path
import json

import pytest

from backend import create_app
from backend.importer.details import CourseReference, DetailImportError
from backend.importer.http import SourceClient, SourceDocument, SourceFetchError
from backend.importer.semester import SemesterViewResult, fetch_semester_details


def views():
    refs = tuple(CourseReference(str(i), f"https://example.invalid/detail/{i}",
                                 f"Fiktiver Kurs {i}", 1, "configured") for i in range(12))
    return (SemesterViewResult("semester", "observed", 12, 0, refs),
            SemesterViewResult("special_dates", "observed", 1, 0, refs[:1]))


@pytest.fixture
def session(monkeypatch):
    html = (Path(__file__).parent / "fixtures/course_detail.html").read_text(encoding="utf-8")
    with SourceClient("https://example.invalid/start") as client:
        calls = []
        def fetch(url):
            calls.append(url)
            return SourceDocument(html, url)
        monkeypatch.setattr(client, "fetch", fetch)
        yield client, calls


def run(client, **kwargs):
    options = dict(semester="WiSe 2025/26", study_key="DEMO", regulations_key="DEMO-PO", budget=12)
    options.update(kwargs)
    return fetch_semester_details(client, views(), **options)


def test_all_known_targets_over_sample_limit_are_checked_once(session):
    client, calls = session
    sample = run(client)
    assert len(calls) == len(set(calls)) == len(sample.details) == 12
    assert sample.unchecked_count == 0
    assert not sample.complete


@pytest.mark.parametrize("budget", [0, 11, 101, True])
def test_budget_rejected_before_detail_fetch(session, budget):
    client, calls = session
    with pytest.raises(DetailImportError):
        run(client, budget=budget)
    assert not calls


def test_wrong_semester_stops_at_first_detail(session):
    client, calls = session
    with pytest.raises(DetailImportError):
        run(client, semester="Fiktives anderes Semester")
    assert len(calls) == 1


def test_missing_context_stops_before_network(session):
    client, calls = session
    with pytest.raises(DetailImportError):
        run(client, semester=None)
    assert not calls


def test_late_failure_returns_no_partial_sample(session, monkeypatch):
    client, calls = session
    original = client.fetch
    def fetch(url):
        if len(calls) == 2:
            raise SourceFetchError("PRIVATE")
        return original(url)
    monkeypatch.setattr(client, "fetch", fetch)
    with pytest.raises(DetailImportError) as error:
        run(client)
    assert len(calls) == 2
    assert "PRIVATE" not in str(error.value)


@pytest.mark.parametrize("failure", [False, True])
def test_cli_details_and_failure_are_sanitized(session, monkeypatch, failure):
    client, _ = session
    for name in ("search_study", "follow_named_result", "submit_labeled_search"):
        monkeypatch.setattr("backend.cli." + name, lambda *a, **k: None)
    monkeypatch.setattr("backend.cli.audit_semester_views", lambda *a, **k: views())
    original = client.fetch
    def fetch(self, url):
        if failure and url.endswith("/2"):
            raise SourceFetchError("PRIVATE")
        return original(url)
    monkeypatch.setattr(SourceClient, "fetch", fetch)
    app = create_app({"TESTING": True, "LSF_BASE_URL": "https://example.invalid/start",
                      "LSF_ID_PARAMETER": "record", "LSF_ID_NAMESPACE": "DEMO"})
    result = app.test_cli_runner().invoke(args=[
        "source-semester-check", "--query", "Demo", "--title", "Demo", "--json", "--details",
        "--semester", "WiSe 2025/26", "--study-key", "DEMO", "--regulations-key", "DEMO-PO",
    ])
    assert result.exit_code == 1
    report = json.loads(result.output)
    assert report["checked_details"] == (0 if failure else 12)
    assert report["normalization_summary"]["preview_count"] == (0 if failure else 12)
    assert report["normalization_summary"]["blocked_count"] == 0
    assert report["schema_version"] == 7
    assert report["review_summary"]["reason_counts"].get("study_context_requires_verification", 0) == (0 if failure else 12)
    assert "semester_extent_unverified" in report["completeness_review"]["blockers"]
    assert not report["completeness_review"]["eligible_for_publication"]
    assert report["known_details_checked"] is not failure
    assert report["status"] == ("failed" if failure else "needs_review")
    assert not report["complete"] and not report["published"]
    assert "PRIVATE" not in result.output and "example.invalid" not in result.output
