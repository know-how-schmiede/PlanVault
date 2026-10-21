"""Belegte Tagesbezeichnungen als feste Codes; keine automatischen Ausfallregeln."""

from dataclasses import dataclass
from datetime import date


NOTICE_LABELS = {
    'Weihnachtsferien': 'christmas_break',
    'Heilige Drei Könige': 'epiphany',
    'unbenannt': 'unnamed',
}
NOTICE_KINDS = frozenset(NOTICE_LABELS.values()) | {'unclassified'}
# Eine erkannte fehlende Bezeichnung ist keine bekannte fachliche Bedeutung.
KNOWN_NOTICE_KINDS = NOTICE_KINDS - {'unnamed', 'unclassified'}


@dataclass(frozen=True)
class DayNotice:
    local_date: str
    kind: str

    def __post_init__(self):
        try:
            day = date.fromisoformat(self.local_date)
        except (ValueError, TypeError):
            raise ValueError('Ungültiger Tageshinweis.') from None
        if (day.isoformat() != self.local_date or not isinstance(self.kind, str) or
                self.kind not in NOTICE_KINDS):
            raise ValueError('Ungültiger Tageshinweis.')


def classify_day_notice(text):
    # Vollständige Übereinstimmung: Zusätze und unbekannte Texte bleiben ungeklärt.
    return NOTICE_LABELS.get(text, 'unclassified')
