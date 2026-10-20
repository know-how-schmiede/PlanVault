"""Verbindet beobachtete Detailnavigation mit Parser und Normalisierung."""

from backend.importer.http import SourceClient
from backend.parser import CalendarPreview, CourseContext, normalize_course, parse_course_detail


def fetch_course_preview(client: SourceClient, observed_link: str, context: CourseContext, *,
                         relative_to: str | None = None) -> CalendarPreview:
    document = client.fetch(observed_link, relative_to=relative_to)
    course = parse_course_detail(document.html, expected_semester=context.semester)
    return normalize_course(course, context)
