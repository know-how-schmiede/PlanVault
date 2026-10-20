from datetime import date, time
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from backend.parser import SourceParseError, parse_course_detail


@pytest.fixture
def detail_html():
    return (Path(__file__).parent / "fixtures" / "course_detail.html").read_text(encoding="utf-8")


def test_observed_structure_preserves_both_series_and_missing_values(detail_html):
    course = parse_course_detail(detail_html, expected_semester="WiSe 2025/26")
    assert course.title == "Fiktives Labor Datenanalyse"
    assert course.source_identifier is None
    assert course.description is None
    assert course.event_type == "Labor"
    assert len(course.series) == 2
    first, second = course.series
    assert (first.weekday, first.start_time, first.end_time) == (0, time(8), time(9, 30))
    assert (first.valid_from, first.valid_until) == (date(2025, 10, 6), date(2026, 1, 19))
    assert first.timezone == "Europe/Berlin"
    assert first.recurrence == "woch"
    assert first.instructor == "Fiktive Lehrperson A"
    assert first.room == "DEMO-Raum A"
    assert second.instructor is None
    assert second.weekday == 2
    assert course.review_reasons == ("missing_source_identifier",)


def test_cancellation_and_unverified_rhythm_are_retained_for_review(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    cells = soup.find_all("table")[1].find_all("tr")[1].find_all("td")
    cells[3].string = "UNGEPRUEFTER-RHYTHMUS"
    cells[8].string = "Fiktive Verlegung, bitte prüfen"
    cells[9].string = "20.10.2025; weitere Ausnahmen siehe Hinweis"
    course = parse_course_detail(str(soup))
    assert course.series[0].recurrence == "UNGEPRUEFTER-RHYTHMUS"
    assert course.series[0].cancellation_text == "20.10.2025; weitere Ausnahmen siehe Hinweis"
    assert set(course.review_reasons) == {
        "unverified_recurrence", "cancellations_require_review", "notes_require_review", "missing_source_identifier",
    }


@pytest.mark.parametrize("html", ["", "<h1>Fehler</h1>", '<input type="password">'])
def test_missing_error_and_login_pages_are_not_empty_plans(html):
    with pytest.raises(SourceParseError):
        parse_course_detail(html)


def test_truncated_or_empty_schedule_is_rejected(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    table = soup.find_all("table")[1]
    for row in table.find_all("tr")[1:]:
        row.decompose()
    with pytest.raises(SourceParseError):
        parse_course_detail(str(soup))


@pytest.mark.parametrize("old,new", [
    ("09:30", "07:30"), ("08:00", "25:00"),
    ("06.10.2025", "31.02.2025"), ("19.01.2026", "01.01.2025"),
    ("Mo.", "unbekannt"), ("Mo.", ""),
])
def test_invalid_time_date_or_weekday_rejects_entire_page(detail_html, old, new):
    with pytest.raises(SourceParseError):
        parse_course_detail(detail_html.replace(old, new, 1))


def test_wrong_semester_is_rejected(detail_html):
    with pytest.raises(SourceParseError):
        parse_course_detail(detail_html, expected_semester="SoSe 2026")


def test_unknown_row_does_not_silently_drop_data(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    row = soup.new_tag("tr")
    cell = soup.new_tag("td", colspan="10")
    cell.string = "Fiktive zusätzliche Gruppe"
    row.append(cell)
    soup.find_all("table")[1].append(row)
    with pytest.raises(SourceParseError):
        parse_course_detail(str(soup))


def test_reordered_columns_are_matched_by_header(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    for row in soup.find_all("table")[1].find_all("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        row.append(cells[5].extract())
    course = parse_course_detail(str(soup))
    assert course.series[0].room == "DEMO-Raum A"
    assert course.series[0].instructor == "Fiktive Lehrperson A"


def test_error_message_does_not_expose_invalid_source_value(detail_html):
    marker = "VERTRAULICHER_TESTWERT"
    with pytest.raises(SourceParseError) as error:
        parse_course_detail(detail_html.replace("08:00", marker, 1))
    assert marker not in str(error.value)


def test_links_and_active_content_are_not_returned(detail_html):
    html = detail_html.replace("DEMO-Raum A", '<a href="https://example.invalid/private">DEMO-Raum A</a>')
    html = html.replace("Fiktives Labor Datenanalyse</h3>", 'Fiktives Labor Datenanalyse<script>UNTRUSTED</script></h3>')
    course = parse_course_detail(html)
    assert course.series[0].room == "DEMO-Raum A"
    assert "example.invalid" not in repr(course)
    assert "UNTRUSTED" not in course.title


def test_optional_number_and_long_description_are_preserved(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    soup.find("th", string="Veranstaltungsnummer").find_next_sibling("td").string = "DEMO-101"
    soup.find("th", string="Langtext").find_next_sibling("td").string = "Fiktive Beschreibung"
    course = parse_course_detail(str(soup))
    assert course.source_identifier == "DEMO-101"
    assert course.description == "Fiktive Beschreibung"
    assert course.title == "Fiktives Labor Datenanalyse"
    assert course.review_reasons == ()


def test_missing_title_is_rejected(detail_html):
    soup = BeautifulSoup(detail_html, "html.parser")
    soup.h3.decompose()
    with pytest.raises(SourceParseError):
        parse_course_detail(str(soup))


def test_synthetic_single_date_is_preserved_but_rhythm_needs_review(detail_html):
    # Zellweise ändern, unabhängig von der Formatierung der Fixture.
    soup = BeautifulSoup(detail_html, "html.parser")
    cells = soup.find_all("table")[1].find_all("tr")[1].find_all("td")
    cells[3].string = "DEMO-EINZEL"
    cells[4].string = "06.10.2025"
    course = parse_course_detail(str(soup))
    assert course.series[0].valid_from == course.series[0].valid_until == date(2025, 10, 6)
    assert "unverified_recurrence" in course.review_reasons
