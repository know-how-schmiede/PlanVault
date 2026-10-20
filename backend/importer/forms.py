"""Konservative Navigation mit beobachteten HTML-Suchformularen."""

from dataclasses import dataclass, field
from urllib.parse import urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from backend.importer.http import SourceClient, SourceDocument


class FormNavigationError(ValueError):
    """Ungeprüfte Formularstruktur; niemals Quellwerte in Fehlermeldungen."""


@dataclass(frozen=True)
class _Control:
    name: str = field(repr=False)
    values: tuple[str, ...] = field(repr=False)
    editable: bool = False
    options: tuple[str, ...] | None = field(default=None, repr=False)
    multiple: bool = False


@dataclass(frozen=True)
class SearchForm:
    action: str = field(repr=False)
    location: str = field(repr=False)
    method: str
    controls: tuple[_Control, ...] = field(repr=False)
    buttons: tuple[tuple[str, str], ...] = field(repr=False)

    def submit(self, client: SourceClient, *, values: dict[str, tuple[str, ...]] | None = None,
               button: tuple[str, str] | None = None) -> SourceDocument:
        """Nur beobachtete Text-/Auswahlfelder überschreiben; hidden unverändert."""
        values = {} if values is None else values
        for name, replacement in values.items():
            matches = [control for control in self.controls if control.name == name]
            if len(matches) != 1 or not matches[0].editable:
                raise FormNavigationError("Eingabefeld fehlt, ist geschützt oder mehrdeutig.")
            control = matches[0]
            if not isinstance(replacement, tuple) or any(not isinstance(v, str) for v in replacement):
                raise FormNavigationError("Feldwerte müssen als Tupel von Textwerten vorliegen.")
            if (not control.multiple and len(replacement) != 1) or len(set(replacement)) != len(replacement):
                raise FormNavigationError("Ungültige Anzahl ausgewählter Werte.")
            if control.options is not None and any(v not in control.options for v in replacement):
                raise FormNavigationError("Auswahlwert wurde von der Quelle nicht angeboten.")
        if button is None and self.buttons:
            raise FormNavigationError("Eine beobachtete Suchschaltfläche muss explizit gewählt werden.")
        if button is not None and self.buttons.count(button) != 1:
            raise FormNavigationError("Suchschaltfläche fehlt oder ist mehrdeutig.")
        pairs = [(control.name, value) for control in self.controls
                 for value in values.get(control.name, control.values)]
        if button is not None and button[0]:
            pairs.append(button)
        target = client.resolve(self.action, relative_to=self.location)
        if self.method == "post":
            return client.fetch(target, form=pairs)
        # Browser ersetzen bei GET die Query des action-Ziels durch Formulardaten.
        parts = urlsplit(target)
        target = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(pairs), ""))
        return client.fetch(target)


def read_search_form(document: SourceDocument, *, required_fields: set[str]) -> SearchForm:
    """Formular anhand bekannter Feldnamen eindeutig auswählen, nie per Index raten.

    Feldnamen kommen aus einer separat geprüften Quellenanalyse zur Laufzeit.
    Keine LSF-Feldnamen oder Navigationsparameter sind hier fest eingebaut.
    """
    if not required_fields or not document.html.strip() or len(document.html) > 2_000_000:
        raise FormNavigationError("Formularauswahl oder Dokument ist ungültig.")
    soup = BeautifulSoup(document.html, "html.parser")
    if soup.find("base") or soup.find("input", attrs={"type": lambda value: value and value.lower() == "password"}):
        raise FormNavigationError("Basisadresse oder Anmeldeseite benötigt manuelle Prüfung.")
    if soup.select("[form]"):
        raise FormNavigationError("Extern zugeordnete Formularfelder werden noch nicht unterstützt.")
    matches = []
    for form in soup.find_all("form"):
        names = {control.get("name") for control in form.find_all(["input", "select", "textarea", "button"])
                 if not control.has_attr("disabled")}
        if required_fields.issubset(names):
            matches.append(form)
    if len(matches) != 1:
        raise FormNavigationError("Suchformular fehlt oder ist nicht eindeutig.")
    form = matches[0]
    method = form.get("method", "get").lower()
    if (method not in {"get", "post"} or
            form.get("enctype", "application/x-www-form-urlencoded").lower() != "application/x-www-form-urlencoded" or
            form.get("accept-charset", "utf-8").lower() != "utf-8"):
        raise FormNavigationError("Formularmethode oder Kodierung wird noch nicht unterstützt.")
    if form.find("form") or form.find("fieldset") or form.has_attr("onsubmit"):
        raise FormNavigationError("Formularstruktur oder Skriptsteuerung benötigt Prüfung.")
    controls, buttons = [], []
    for element in form.find_all(["input", "select", "textarea", "button"]):
        if element.has_attr("disabled"):
            continue
        if any(attr in element.attrs for attr in ("formaction", "formmethod", "formenctype", "onclick", "onchange")):
            raise FormNavigationError("Abweichende Formularsteuerung benötigt Prüfung.")
        name = element.get("name", "")
        kind = element.get("type", "submit" if element.name == "button" else "text").lower()
        if element.name == "button" or (element.name == "input" and kind in {"submit", "reset", "button"}):
            if kind == "submit":
                buttons.append((name, element.get("value", "")))
            continue
        if element.name == "input" and kind not in {"text", "search", "hidden", "checkbox", "radio"}:
            raise FormNavigationError("Unbekannter Eingabetyp im Suchformular.")
        if not name:
            continue
        if element.name == "select":
            options = [option for option in element.find_all("option")
                       if not option.has_attr("disabled") and
                       not (option.find_parent("optgroup") and option.find_parent("optgroup").has_attr("disabled"))]
            if any(option.has_attr("selected") and option not in options for option in element.find_all("option")):
                raise FormNavigationError("Deaktivierte Vorauswahl benötigt Prüfung.")
            if any(option.has_attr("selected") and option not in options for option in element.find_all("option")):
                raise FormNavigationError("Deaktivierte Vorauswahl benötigt Prüfung.")
            option_values = tuple(option.get("value", option.get_text(strip=True)) for option in options)
            if len(option_values) != len(set(option_values)):
                raise FormNavigationError("Mehrdeutige Auswahlwerte.")
            selected = tuple(option.get("value", option.get_text(strip=True))
                             for option in options if option.has_attr("selected"))
            multiple = element.has_attr("multiple")
            if not multiple and len(selected) > 1:
                raise FormNavigationError("Mehrdeutige Vorauswahl.")
            if not multiple and not selected:
                selected = option_values[:1]
            controls.append(_Control(name, selected, True, option_values, multiple))
        elif element.name == "textarea":
            value = element.get_text().replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
            controls.append(_Control(name, (value,), not element.has_attr("readonly")))
        else:
            default = "on" if kind in {"checkbox", "radio"} else ""
            value = element.get("value", default)
            chosen = (value,) if kind not in {"checkbox", "radio"} or element.has_attr("checked") else ()
            controls.append(_Control(name, chosen, kind in {"text", "search"} and not element.has_attr("readonly")))
    return SearchForm(form.get("action", ""), document.location, method, tuple(controls), tuple(buttons))
