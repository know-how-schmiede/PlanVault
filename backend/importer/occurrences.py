"""Strikter taggenauer Planblock-Parser; Quelldaten bleiben nur im Speicher."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

from backend.importer.details import DetailImportError, collect_course_references
from backend.importer.http import SourceDocument
from backend.importer.navigation import _page, _caption
from backend.importer.structure import COURSE_BLOCK_SELECTOR


@dataclass(frozen=True)
class ObservedOccurrence:
    reference_key: str
    local_date: str
    start_time: str
    end_time: str
    room: str | None = field(repr=False)
    event_type: str = field(repr=False)
    # Die Quelle hat keine verifiziert zugeordnete Gruppenspalte.
    supplementary_text: str = field(repr=False)


def _positions(table):
    """Tabellenkoordinaten einschließlich rowspan/colspan, ohne verschachtelte Zeilen."""
    occupied, positions = {}, {}
    rows = [r for r in table.find_all('tr') if r.find_parent('table') is table]
    if len(rows) > 2000:
        raise DetailImportError('Planraster überschreitet die erlaubte Größe.')
    for y, row in enumerate(rows):
        x = 0
        for cell in row.find_all(['td', 'th'], recursive=False):
            while (y, x) in occupied:
                x += 1
            try:
                width, height = int(cell.get('colspan', 1)), int(cell.get('rowspan', 1))
            except (ValueError, TypeError):
                raise DetailImportError('Ungültige Zellspanne im Planraster.') from None
            if not (1 <= width <= 32 and 1 <= height <= 2000 and x + width <= 32):
                raise DetailImportError('Unbekannte Zellspanne im Planraster.')
            positions[id(cell)] = (x, width)
            for dy in range(min(height, len(rows) - y)):
                for dx in range(width):
                    key = (y + dy, x + dx)
                    if key in occupied or len(occupied) >= 64000:
                        raise DetailImportError('Widersprüchliches Planraster.')
                    occupied[key] = True
            x += width
    return positions


def read_week_occurrences(client, document, result, *, identity_policy):
    """Datum aus der Tageskolumne, Zeiten/Raum aus dem jeweiligen achtzeiligen Block."""
    from datetime import date
    soup = _page(document)
    monday = date.fromisocalendar(result.iso_year, result.iso_week, 1)
    events = []
    grids = {}
    for block in soup.select(COURSE_BLOCK_SELECTOR):
        table = block.find_parent('table')
        parent = table.find_parent('td') if table else None
        outer = parent.find_parent('table') if parent else None
        if outer is None:
            raise DetailImportError('Veranstaltungsblock ohne eindeutige Tageskolumne.')
        if id(outer) not in grids:
            positions = _positions(outer)
            columns = {}
            for th in outer.find_all('th'):
                if th.find_parent('table') is not outer:
                    continue
                for offset in range(7):
                    day = monday + timedelta(days=offset)
                    # inspect_week hat Tagesnamen und Datum bereits geprüft.
                    if re.match(r'^\S+\s+' + re.escape(day.strftime('%d.%m.%Y')) + r'(?:\s|$)', _caption(th)):
                        pos, width = positions[id(th)]
                        if width != 1 or pos in columns:
                            raise DetailImportError('Mehrdeutige Tageskolumne.')
                        columns[pos] = day
            if len(columns) not in (5, 7):
                raise DetailImportError('Tageskolumnen sind nicht vollständig zugeordnet.')
            grids[id(outer)] = positions, columns
        positions, columns = grids[id(outer)]
        pos, width = positions[id(parent)]
        if width != 1 or pos not in columns:
            raise DetailImportError('Veranstaltungsblock liegt außerhalb einer Tageskolumne.')
        rows = [r for r in table.find_all('tr') if r.find_parent('table') is table]
        reference = collect_course_references(client, (SourceDocument(str(table), document.location),),
                                               identity_policy=identity_policy)[0]
        texts = [re.sub(r'https?://\S+', '[Adresse entfernt]', _caption(row), flags=re.I) for row in rows]
        times = re.fullmatch(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s+\(([^()]+)\)', texts[1])
        beginning = re.fullmatch(r'Start:\s*(\d{2}\.\d{2}\.\d{4})', texts[2])
        ending = re.fullmatch(r'Ende:\s*(\d{2}\.\d{2}\.\d{4})', texts[3])
        room = re.fullmatch(r'Raum:\s*(.*)', texts[4])
        if not (times and beginning and ending and room) or texts[7]:
            raise DetailImportError('Unbekannte Felder im Veranstaltungsblock.')
        try:
            start, end = (datetime.strptime(t, '%H:%M').time() for t in times.groups()[:2])
            first, last = (datetime.strptime(m[1], '%d.%m.%Y').date() for m in (beginning, ending))
        except ValueError:
            raise DetailImportError('Ungültiges Datum oder Uhrzeit im Veranstaltungsblock.') from None
        day = columns[pos]
        if start >= end or not first <= day <= last:
            raise DetailImportError('Veranstaltungsblock liegt außerhalb seines Zeitraums.')
        events.append(ObservedOccurrence(reference.key, day.isoformat(), start.isoformat(),
                                         end.isoformat(), room[1] or None, texts[5], texts[6]))
    return tuple(events)
