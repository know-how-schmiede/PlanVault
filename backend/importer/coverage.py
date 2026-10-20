"""Abgleich erwarteter ISO-Wochen; allein noch keine Importfreigabe."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class WeekResult:
    iso_year: int
    iso_week: int
    # Nur der Adapter darf nach Strukturprüfung ok oder empty_confirmed melden.
    status: str


@dataclass(frozen=True)
class Coverage:
    missing: tuple[tuple[int, int], ...]
    unexpected: tuple[tuple[int, int], ...]
    failed: tuple[tuple[int, int], ...]
    duplicates: tuple[tuple[int, int], ...]

    @property
    def weeks_complete(self) -> bool:
        return not (self.missing or self.unexpected or self.failed or self.duplicates)


def check_week_coverage(start: date, end: date, results: list[WeekResult]) -> Coverage:
    if not 0 <= (end - start).days <= 370:
        raise ValueError("Ungültiger Semesterzeitraum.")
    monday = start - timedelta(days=start.weekday())
    expected = set()
    while monday <= end:
        year, week, _ = monday.isocalendar()
        expected.add((year, week))
        monday += timedelta(days=7)
    seen, failed, duplicates = set(), set(), set()
    for result in results:
        try:
            date.fromisocalendar(result.iso_year, result.iso_week, 1)
        except ValueError:
            raise ValueError("Ungültige ISO-Woche.") from None
        key = result.iso_year, result.iso_week
        if key in seen:
            duplicates.add(key)
        seen.add(key)
        if result.status not in {"ok", "empty_confirmed"}:
            failed.add(key)
    return Coverage(*(tuple(sorted(values)) for values in (expected - seen, seen - expected, failed, duplicates)))
