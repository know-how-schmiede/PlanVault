"""Explizite, lokale Semesterregeln; keine vermuteten Ferien oder stillen Korrekturen."""
from dataclasses import dataclass, asdict, replace
from datetime import date
import hashlib
import json
import re

from backend.importer.details import DetailImportError


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def series_digest(series):
    return digest({k: v.isoformat() if hasattr(v, 'isoformat') else v for k, v in asdict(series).items()})


@dataclass(frozen=True)
class CalendarPolicy:
    semester: str
    study_key: str
    regulations_key: str
    study_title: str
    start: date
    end: date
    breaks: tuple
    annotation_rules: tuple = ()

    def to_dict(self):
        return {'schema': 1, 'semester': self.semester, 'study_key': self.study_key,
                'regulations_key': self.regulations_key, 'study_title': self.study_title,
                'start': self.start.isoformat(), 'end': self.end.isoformat(),
                'breaks': list(self.breaks), 'annotation_rules': list(self.annotation_rules)}

    def is_break(self, day):
        return any(row['start'] <= day <= row['end'] for row in self.breaks)


def parse_policy(data):
    try:
        required = {'schema', 'semester', 'study_key', 'regulations_key', 'study_title', 'start', 'end', 'breaks'}
        if (not isinstance(data, dict) or not required <= data.keys() or
                data.keys() - required - {'annotation_rules'} or type(data['schema']) is not int or data['schema'] != 1):
            raise ValueError
        for key in ('semester', 'study_title'):
            if (not isinstance(data[key], str) or not data[key].strip() or len(data[key]) > 200 or
                    re.search(r'https?://', data[key], re.I)):
                raise ValueError
        for key in ('study_key', 'regulations_key'):
            if not isinstance(data[key], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', data[key]):
                raise ValueError
        start, end = date.fromisoformat(data['start']), date.fromisoformat(data['end'])
        if data['start'] != start.isoformat() or data['end'] != end.isoformat():
            raise ValueError
        if not 0 <= (end-start).days <= 370:
            raise ValueError
        if not isinstance(data['breaks'], list) or len(data['breaks']) > 100:
            raise ValueError
        previous = None
        for row in data['breaks']:
            if not isinstance(row, dict) or set(row) != {'start', 'end', 'evidence'}:
                raise ValueError
            a, b = date.fromisoformat(row['start']), date.fromisoformat(row['end'])
            if row['start'] != a.isoformat() or row['end'] != b.isoformat():
                raise ValueError
            if not start <= a <= b <= end or previous is not None and a <= previous:
                raise ValueError
            previous = b
            # Referenznummer/Titel eines extern geprüften Belegs, keine Quelladresse.
            if not isinstance(row['evidence'], str) or not re.fullmatch(r'[\w .,/()–-]{1,200}', row['evidence']):
                raise ValueError
        rules = data.get('annotation_rules', [])
        if not isinstance(rules, list) or len(rules) > 100:
            raise ValueError
        seen = set()
        for rule in rules:
            if (not isinstance(rule, dict) or set(rule) != {'series_digest', 'field', 'effect'} or
                    not re.fullmatch(r'[a-f0-9]{64}', rule['series_digest']) or
                    rule['field'] not in {'note', 'execution_note'} or rule['effect'] != 'annotation' or
                    (rule['series_digest'], rule['field']) in seen):
                raise ValueError
            seen.add((rule['series_digest'], rule['field']))
        return CalendarPolicy(data['semester'], data['study_key'], data['regulations_key'], data['study_title'],
                               start, end, tuple(data['breaks']), tuple(rules))
    except (ValueError, TypeError, KeyError, OverflowError):
        raise DetailImportError('Ungültige Kalenderregeldatei; Schema, Zeitraum und Belege prüfen.') from None


def apply_annotation_rules(course, policy):
    """Nur exakt geprüfte Serienhinweise als Annotation behandeln; Original bleibt erhalten."""
    used, series = set(), []
    for item in course.series:
        fingerprint = series_digest(item)
        changes = {}
        for rule in policy.annotation_rules:
            if rule['series_digest'] == fingerprint:
                if not getattr(item, rule['field']):
                    raise DetailImportError('Hinweisregel trifft auf ein leeres Feld.')
                changes[rule['field']] = None
                used.add((fingerprint, rule['field']))
        series.append(replace(item, **changes))
    return replace(course, series=tuple(series)), used
