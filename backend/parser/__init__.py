"""Normalisierung und Validierung bereits geladener Quelldaten."""

from backend.parser.course import CourseDetail, SourceParseError, parse_course_detail

__all__ = ["CourseDetail", "SourceParseError", "parse_course_detail"]
