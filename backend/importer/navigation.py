"""Navigation über sichtbare Beschriftungen statt eingebetteter Quellparameter."""

from bs4 import BeautifulSoup

from backend.importer.forms import FormNavigationError, read_search_form
from backend.importer.http import SourceClient, SourceDocument


def _page(document):
    if not document.html.strip() or len(document.html) > 2_000_000:
        raise FormNavigationError("Navigationsdokument fehlt oder ist zu groß.")
    soup = BeautifulSoup(document.html, "html.parser")
    if soup.find("base") or soup.select('input[type="password" i]'):
        raise FormNavigationError("Basisadresse oder Anmeldung benötigt Prüfung.")
    return soup


def _caption(element):
    return " ".join(element.get_text(" ", strip=True).split())


def submit_labeled_search(client: SourceClient, document: SourceDocument, *,
                          field_label: str, button_caption: str,
                          search_text: str | None = None) -> SourceDocument:
    """Eindeutige label/for-Zuordnung und benannte Suchschaltfläche verwenden."""
    soup = _page(document)
    labels = [label for label in soup.find_all("label") if _caption(label) == field_label]
    if len(labels) != 1 or not labels[0].get("for"):
        raise FormNavigationError("Suchfeld-Beschriftung fehlt oder ist mehrdeutig.")
    elements = soup.find_all(id=labels[0]["for"])
    if len(elements) != 1:
        raise FormNavigationError("Suchfeld-Zuordnung fehlt oder ist mehrdeutig.")
    element = elements[0]
    form = element.find_parent("form")
    if (form is None or element.has_attr("disabled")
            or labels[0].find_parent("form") is not form):
        raise FormNavigationError("Suchfeld gehört nicht eindeutig zum Formular.")
    if search_text is not None and not element.get("name"):
        raise FormNavigationError("Suchfeld kann nicht überschrieben werden.")
    names = {control["name"] for control in form.find_all(["input", "select", "textarea", "button"])
             if control.get("name") and not control.has_attr("disabled")}
    parsed = read_search_form(document, required_fields=names)
    choices = set()
    for button in form.find_all(["input", "button"]):
        kind = button.get("type", "submit" if button.name == "button" else "text").lower()
        caption = button.get("value", "") if button.name == "input" else _caption(button)
        if kind == "submit" and not button.has_attr("disabled") and caption == button_caption:
            choices.add((button.get("name", ""), button.get("value", "")))
    if len(choices) != 1:
        raise FormNavigationError("Suchschaltfläche fehlt oder ist nicht eindeutig.")
    values = {} if search_text is None else {element["name"]: (search_text,)}
    return parsed.submit(client, values=values, button=choices.pop())


def follow_named_result(client: SourceClient, document: SourceDocument, *,
                        title: str) -> SourceDocument:
    """Exakt benannten Treffer wählen; unterschiedliche Ziele niemals erraten."""
    soup = _page(document)
    title = " ".join(title.split())
    if not title:
        raise FormNavigationError("Trefferbezeichnung fehlt.")
    links = [link for link in soup.find_all("a", href=True) if _caption(link) == title]
    if not links or any(link.has_attr("onclick") for link in links):
        raise FormNavigationError("Treffer fehlt oder benötigt Skriptsteuerung.")
    targets = {client.resolve(link["href"], relative_to=document.location) for link in links}
    if len(targets) != 1:
        raise FormNavigationError("Treffername ist nicht eindeutig; Studiengang und Prüfungsordnung prüfen.")
    return client.fetch(targets.pop())


def search_study(client: SourceClient, query: str) -> SourceDocument:
    """Beobachteter Einstieg in die Studiengangsauswahl; noch kein Semesterimport."""
    if not query.strip() or len(query) > 200:
        raise FormNavigationError("Studiengangsuche benötigt einen kurzen Suchtext.")
    return submit_labeled_search(client, client.fetch(), field_label="Studiengang",
                                 button_caption="Auswahl", search_text=query)
