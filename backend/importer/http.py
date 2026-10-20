"""Begrenzter HTTP-Zugriff; Quelladressen und Cookies bleiben im Arbeitsspeicher."""

from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from http.client import HTTPException
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPCookieProcessor, Request, build_opener


class SourceFetchError(ValueError):
    """Bereinigter Fehler ohne Quelladresse, Antworttext oder Sitzungsdaten."""


@dataclass(frozen=True)
class SourceDocument:
    html: str = field(repr=False)
    location: str = field(repr=False)


class _Redirects(HTTPRedirectHandler):
    max_redirections = 4
    max_repeats = 2

    def __init__(self, client):
        self.client = client

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.client.resolve(newurl, relative_to=req.full_url)
        # POST darf nicht stillschweigend umgeleitet oder wiederholt werden.
        if req.get_method() != "GET":
            raise SourceFetchError("Weiterleitung einer Formularanfrage benötigt Prüfung.")
        request = super().redirect_request(req, fp, code, msg, headers, newurl)
        if request is not None:
            self.client._before_request()
        return request


class SourceClient:
    """Eine begrenzte Sitzung pro manueller Importoperation.

    Die konfigurierte HTTPS-Adresse ist die Vertrauensgrenze. Interne Hosts sind
    zulässig; gefundene Links und Redirects müssen exakt denselben Origin nutzen.
    Nur aus Quellantworten gelesene Links übergeben, keine Endpunkte erraten.
    """

    def __init__(self, base_url: str, *, timeout: float = 10, interval: float = 1,
                 max_requests: int = 20, retries: int = 2, max_bytes: int = 2_000_000):
        if not (0 < timeout <= 60 and 0.1 <= interval <= 60 and
                1 <= max_requests <= 100 and 0 <= retries <= 3 and 1 <= max_bytes <= 2_000_000):
            raise SourceFetchError("Ungültige Abrufgrenzen.")
        self._origin = self._url_origin(base_url)
        self._base_url = base_url
        self.timeout, self.interval = timeout, interval
        self.max_requests, self.retries, self.max_bytes = max_requests, retries, max_bytes
        self._count = 0
        self._last_request = None
        self._cookies = CookieJar()
        self._opener = build_opener(_Redirects(self), HTTPCookieProcessor(self._cookies))
        self._closed = False

    @staticmethod
    def _url_origin(url):
        try:
            if not isinstance(url, str) or any(ord(char) <= 32 or ord(char) == 127 for char in url):
                raise ValueError
            # Unkodierte Unicode-URLs verursachen sonst unsanitisierte HTTP-Fehler.
            url.encode("ascii")
            parsed = urlsplit(url)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                    or parsed.password is not None or parsed.fragment or "\\" in url):
                raise ValueError
            return parsed.hostname.lower(), parsed.port or 443
        except (TypeError, ValueError, UnicodeError):
            raise SourceFetchError("Gültige HTTPS-Quellkonfiguration ohne Zugangsdaten erforderlich.") from None

    def resolve(self, link: str, *, relative_to: str | None = None) -> str:
        if not isinstance(link, str) or any(ord(char) <= 32 for char in link):
            raise SourceFetchError("Ungültiger Navigationslink.")
        base = relative_to if relative_to is not None else self._base_url
        if self._url_origin(base) != self._origin:
            raise SourceFetchError("Navigation außerhalb der konfigurierten Quelle abgelehnt.")
        try:
            target = urljoin(base, link)
        except ValueError:
            raise SourceFetchError("Ungültiger Navigationslink.") from None
        if self._url_origin(target) != self._origin:
            raise SourceFetchError("Navigation außerhalb der konfigurierten Quelle abgelehnt.")
        return target

    def _before_request(self):
        if self._closed or self._count >= self.max_requests:
            raise SourceFetchError("Sitzung geschlossen oder Abruflimit erreicht.")
        now = time.monotonic()
        if self._last_request is not None:
            time.sleep(max(0, self.interval - (now - self._last_request)))
        self._count += 1
        self._last_request = time.monotonic()

    def fetch(self, link: str | None = None, *, relative_to: str | None = None,
              form: list[tuple[str, str]] | None = None) -> SourceDocument:
        """GET oder explizites POST für ein zuvor beobachtetes Suchformular.

        Formularwerte/-ziele werden vom Aufrufer aus der Antwort gelesen.
        POST wird niemals automatisch wiederholt.
        """
        target = self.resolve(self._base_url if link is None else link, relative_to=relative_to)
        data = urlencode(form).encode("utf-8") if form is not None else None
        request = Request(target, data=data, headers={
            "User-Agent": "PlanVault-SourceCheck",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Encoding": "identity",
        })
        attempts = self.retries + 1 if form is None else 1
        for attempt in range(attempts):
            self._before_request()
            retryable = False
            try:
                with self._opener.open(request, timeout=self.timeout) as response:
                    final_url = self.resolve(response.geturl())
                    if response.status != 200:
                        raise SourceFetchError("Unerwarteter HTTP-Antwortstatus.")
                    if response.headers.get_content_type() not in {"text/html", "application/xhtml+xml"}:
                        raise SourceFetchError("Quelle liefert kein HTML-Dokument.")
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise SourceFetchError("Nicht unterstützte Antwortkomprimierung.")
                    body = response.read(self.max_bytes + 1)
                    if len(body) > self.max_bytes:
                        raise SourceFetchError("Quelldokument überschreitet die erlaubte Größe.")
                    try:
                        html = body.decode(response.headers.get_content_charset() or "utf-8")
                    except (UnicodeError, LookupError):
                        raise SourceFetchError("Zeichenkodierung der Quelle ist nicht lesbar.") from None
                    if not html.strip():
                        raise SourceFetchError("Leere Quellantwort.")
                    return SourceDocument(html, final_url)
            except HTTPError as error:
                retryable = error.code in {429, 502, 503, 504}
                error.close()
            except (URLError, TimeoutError, OSError, HTTPException):
                retryable = True
            if not retryable or attempt + 1 == attempts:
                raise SourceFetchError("Quellabruf fehlgeschlagen; Verbindung oder Zugang prüfen.") from None
            time.sleep(min(2 ** attempt, 4))
        raise SourceFetchError("Quellabruf fehlgeschlagen.")

    def close(self):
        self._cookies.clear()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
