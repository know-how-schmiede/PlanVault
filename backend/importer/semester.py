"""Begrenzte Bestandsaufnahme zusätzlicher Semesteransichten."""

from dataclasses import dataclass, field

from backend.importer.details import collect_course_references, CourseReference
from backend.importer.forms import FormNavigationError
from backend.importer.identity import SourceIdentityPolicy
from backend.importer.navigation import _page, _caption
from backend.importer.weeks import read_week_menu


VIEWS = (
    ("semester", "Semesteransicht"),
    ("special_dates", "Semesterzeitansicht nur Block/Einzeltermine"),
)


@dataclass(frozen=True)
class SemesterViewResult:
    view: str
    status: str
    reference_count: int
    additional_count: int
    references: tuple[CourseReference, ...] = field(repr=False)


def audit_semester_views(client, document, *, identity_policy: SourceIdentityPolicy):
    """Zwei Ansichten sequenziell prüfen; keine Detailabrufe oder Freigabe.

    Leere Ansichten gelten nicht als bestätigter Leerbestand. Die zweite Ansicht
    wird gegen die erste verglichen, damit zusätzliche Ziele sichtbar bleiben.
    """
    if not isinstance(identity_policy, SourceIdentityPolicy):
        raise FormNavigationError("Semesterprüfung benötigt eine konfigurierte Quellkennung.")
    initial = read_week_menu(document)
    expected_weeks = tuple(c.key for c in initial.choices)
    results = []
    known = set()
    for code, label in VIEWS:
        menu = read_week_menu(document)
        soup = _page(document)
        selects = soup.find_all("select", attrs={"name": menu.field_name})
        if len(selects) != 1:
            raise FormNavigationError("Ansichtsauswahl ist mehrdeutig.")
        options = selects[0].find_all("option")
        matches = [o for o in options if _caption(o) == label]
        if (len(matches) != 1 or not matches[0].get("value") or
                matches[0].has_attr("disabled") or
                sum(o.get("value") == matches[0].get("value") for o in options) != 1):
            raise FormNavigationError("Semesteransicht fehlt oder ist mehrdeutig.")
        document = menu.form.submit(client, values={menu.field_name: (matches[0]["value"],)},
                                    button=menu.button)
        returned = read_week_menu(document)
        if tuple(c.key for c in returned.choices) != expected_weeks:
            raise FormNavigationError("Wochenangebot hat sich während der Semesterprüfung geändert.")
        soup = _page(document)
        selects = soup.find_all("select", attrs={"name": returned.field_name})
        selected = selects[0].find_all("option", selected=True) if len(selects) == 1 else []
        if len(selected) != 1 or _caption(selected[0]) != label:
            raise FormNavigationError("Quelle hat die angeforderte Semesteransicht nicht übernommen.")
        refs = (collect_course_references(client, (document,), identity_policy=identity_policy)
                if soup.select("td.plan5a") else ())
        keys = {r.key for r in refs}
        results.append(SemesterViewResult(code, "observed" if refs else "empty_unverified",
                                         len(refs), len(keys - known) if results else 0, refs))
        known.update(keys)
    return tuple(results)
