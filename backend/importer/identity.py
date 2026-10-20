"""Konfigurierte Quellkennung ohne Speicherung von URLs oder Parameternamen."""

from dataclasses import dataclass, field
import hashlib
import json
import re
from urllib.parse import parse_qs, urlsplit

from backend.importer.http import SourceClient, SourceFetchError


class SourceIdentityError(ValueError):
    """Quellkennung fehlt oder ist mehrdeutig; ausschließlich bereinigte Meldungen."""


@dataclass(frozen=True)
class SourceIdentityPolicy:
    parameter: str = field(repr=False)
    namespace: str = field(repr=False)

    def __post_init__(self):
        if (not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,127}", self.parameter) or
                not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", self.namespace)):
            raise SourceIdentityError("Ungültige Konfiguration der Quellkennung.")

    def key_for(self, client: SourceClient, target: str) -> str:
        try:
            resolved = client.resolve(target)
            parts = urlsplit(resolved)
            values = parse_qs(parts.query, keep_blank_values=True, max_num_fields=100).get(self.parameter, [])
            if len(values) != 1 or not re.fullmatch(r"[1-9][0-9]{0,31}", values[0]):
                raise SourceIdentityError("Eindeutige numerische Quellkennung fehlt.")
            payload = ["source-event-v1", self.namespace, parts.hostname.lower(), parts.port or 443, values[0]]
            return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()
        except (SourceFetchError, ValueError):
            raise SourceIdentityError("Quellkennung konnte nicht sicher gelesen werden.") from None


def configured_identity(parameter: str, namespace: str) -> SourceIdentityPolicy | None:
    if not parameter and not namespace:
        return None
    if not parameter or not namespace:
        raise SourceIdentityError("Quellkennung benötigt Parameter und lokalen Namensraum.")
    return SourceIdentityPolicy(parameter, namespace)
