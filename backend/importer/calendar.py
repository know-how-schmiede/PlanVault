"""Vollständiger Importauftrag mit Regeln, Einzelfeldabgleich und gebundener Prüfliste."""
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime
import re
from zoneinfo import ZoneInfo

from backend.importer.calendar_policy import digest, series_digest, apply_annotation_rules
from backend.importer.comparison import run_view_comparison
from backend.importer.details import DetailImportError
from backend.importer.occurrences import read_week_occurrences
from backend.parser.normalize import normalize_course, CourseContext, NormalizationError

ZONE = ZoneInfo('Europe/Berlin')


def _series_dict(item):
    return {k: v.isoformat() if hasattr(v, 'isoformat') else v for k, v in asdict(item).items()}


def _signature(key, day, start, end, room, kind):
    return key, day, start, end, room or '', kind


def build_candidate(policy, references, sample, observations, audit):
    """Harte Fehler bleiben nicht überstimmbar; fachliche Prüfung bindet den ganzen Inhalt."""
    hard, reviews, events, suppressed, inventory = [], [], [], [], []
    if (audit['status'] == 'failed' or not audit['all_requested_weeks_observed'] or
            audit['unavailable_weeks'] or audit['failed_weeks'] or
            not audit['comparison'] or not audit['comparison']['reference_sets_equal']):
        hard.append({'code': 'source_inventory_incomplete'})
    keys = [r.key for r in references]
    if (not keys or len(keys) != len(set(keys)) or sample.unchecked_count or
            keys != [d.reference_key for d in sample.details]):
        raise DetailImportError('Widersprüchlicher Kalenderimportbestand.')
    allowed = set(keys)
    if any(o.reference_key not in allowed for o in observations):
        raise DetailImportError('Unbekannte Veranstaltung im Einzelterminabgleich.')
    # Nur eindeutige Aliasauflösung auf einen tatsächlich vorhandenen Detail-Raumcode.
    detail_rooms = {d.reference_key: {s.room or '' for s in d.source_course.series}
                    for d in sample.details if d.source_course is not None}
    room_aliases = set()

    def room_code(observation):
        raw = observation.room or ''
        known = detail_rooms.get(observation.reference_key, set())
        if raw in known:
            return raw
        matches = [room for room in known if room and
                   (raw.endswith(' -'+room) or raw.endswith(' - '+room))]
        if len(matches) == 1:
            room_aliases.add((observation.reference_key, raw, matches[0]))
            return matches[0]
        return raw

    remaining = Counter(_signature(o.reference_key, o.local_date, o.start_time, o.end_time, room_code(o), o.event_type)
                        for o in observations if policy.start.isoformat() <= o.local_date <= policy.end.isoformat())
    used_rules = set()
    for number, detail in enumerate(sample.details, 1):
        course = detail.source_course
        if course is None:
            raise DetailImportError('Originale Terminserien für die Prüfung fehlen.')
        inventory.append({'detail_number': number, 'title': course.title, 'event_type': course.event_type,
                          'semester': course.semester,
                          'series': [dict(_series_dict(s), series_digest=series_digest(s)) for s in course.series]})
        edited, used = apply_annotation_rules(course, policy)
        used_rules.update(used)
        try:
            preview = normalize_course(edited, CourseContext(detail.reference_key, policy.study_key,
                                       policy.regulations_key, policy.semester, True))
        except NormalizationError as error:
            hard.append({'code': error.code, 'detail_number': number})
            continue
        if detail.requires_review or used:
            reviews.append({'code': 'course_notes', 'detail_number': number,
                            'reasons': list(preview.review_reasons)})
        for occurrence in preview.occurrences:
            day = date.fromisoformat(occurrence.local_date)
            if not policy.start <= day <= policy.end:
                hard.append({'code': 'occurrence_outside_semester', 'detail_number': number,
                             'local_date': occurrence.local_date})
                continue
            start, end = (datetime.fromisoformat(v).astimezone(ZONE).time().isoformat()
                          for v in (occurrence.starts_at, occurrence.ends_at))
            source = course.series[occurrence.series_index]
            signature = _signature(detail.reference_key, occurrence.local_date, start, end,
                                   occurrence.room, course.event_type)
            # Explizite Klausurzeit hat Vorrang vor der unveränderten Quellblockzeit.
            raw_signature = _signature(detail.reference_key, occurrence.local_date,
                                      source.start_time.isoformat(), source.end_time.isoformat(),
                                      source.room, course.event_type)
            matched = signature if remaining[signature] else raw_signature if remaining[raw_signature] else None
            if matched:
                remaining[matched] -= 1
            elif day.weekday() < 5:
                if source.recurrence == 'woch' and policy.is_break(occurrence.local_date):
                    suppressed.append({'detail_number': number, 'series_index': occurrence.series_index,
                                       'local_date': occurrence.local_date, 'reason': 'explicit_academic_break'})
                    continue
                hard.append({'code': 'occurrence_fields_mismatch', 'detail_number': number,
                             'series_index': occurrence.series_index, 'local_date': occurrence.local_date})
            events.append({'course_key': preview.course_key, 'series_index': occurrence.series_index,
                           'title': preview.title, 'start': occurrence.starts_at, 'end': occurrence.ends_at,
                           'room': occurrence.room or '', 'instructor': occurrence.instructor or '',
                           'event_type': course.event_type, 'group': source.execution_note or '', 'review': False})
    for signature, count in remaining.items():
        if count:
            hard.append({'code': 'unexpected_source_occurrence', 'detail_number': keys.index(signature[0])+1,
                         'local_date': signature[1], 'count': count})
    if room_aliases:
        reviews.append({'code': 'room_labels', 'alias_count': len(room_aliases)})
    required_rules = {(r['series_digest'], r['field']) for r in policy.annotation_rules}
    if required_rules != used_rules:
        hard.append({'code': 'unused_annotation_rules'})
    if len(events) > 20000:
        hard.append({'code': 'calendar_too_large'})
    if not events:
        hard.append({'code': 'empty_calendar'})
    # Die Fünftagesansicht beweist weder Wochenendfreiheit noch Gruppenzuordnung.
    reviews.extend([{'code': 'weekend_inventory', 'detail_count': len(inventory)},
                    {'code': 'groups_and_instructors'}, {'code': 'semester_and_study_context'},
                    {'code': 'academic_break_policy'}])
    for notice in audit['unresolved_day_notices']:
        if notice['kind'] != 'unnamed' or not policy.is_break(notice['local_date']):
            reviews.append(dict(notice, code='source_day_notice'))
    for item in reviews:
        item['id'] = digest(item)
    observed_inventory = [dict(asdict(o), reference_key=keys.index(o.reference_key)+1,
                               supplementary_text=re.sub(r'https?://\S+', '[Adresse entfernt]',
                                                         o.supplementary_text, flags=re.I)) for o in observations]
    candidate = {'schema': 1, 'policy': policy.to_dict(), 'events': sorted(events, key=lambda e: (e['start'], e['course_key'], e['series_index'])),
                 'suppressed': suppressed, 'inventory': inventory, 'observations': observed_inventory,
                 'hard_blockers': hard, 'reviews': reviews,
                 'audit': audit, 'complete': False}
    candidate['digest'] = digest(candidate)
    return candidate


def run_calendar_import(client, *, query, policy, identity_policy, detail_budget=80):
    observed, collected = [], []

    def week(document, result):
        observed.extend(read_week_occurrences(client, document, result, identity_policy=identity_policy))

    def details(references, sample):
        collected.append((references, sample))

    audit = run_view_comparison(client, query=query, title=policy.study_title,
                                start=policy.start, end=policy.end, identity_policy=identity_policy,
                                details=True, semester=policy.semester, study_key=policy.study_key,
                                regulations_key=policy.regulations_key, detail_budget=detail_budget,
                                on_observed_week=week, on_details=details, week_budget=54)
    if audit['status'] == 'failed' or not collected:
        raise DetailImportError('Kalenderimport abgebrochen; Quelle oder Struktur ungeklärt.')
    return build_candidate(policy, *collected[0], tuple(observed), audit)


def validate_review(candidate, approval):
    """Kein pauschales complete-Flag; alle einzelnen Fachbefunde exakt bestätigen."""
    try:
        payload = {k: v for k, v in candidate.items() if k != 'digest'}
        if (candidate['digest'] != digest(payload) or candidate['complete'] is not False or
                candidate['hard_blockers'] or not candidate['events']):
            raise ValueError
        if (set(approval) != {'schema', 'candidate_digest', 'decisions'} or type(approval['schema']) is not int or
                approval['schema'] != 1 or approval['candidate_digest'] != candidate['digest']):
            raise ValueError
        decisions = approval['decisions']
        if not isinstance(decisions, dict) or set(decisions) != {r['id'] for r in candidate['reviews']}:
            raise ValueError
        for decision in decisions.values():
            if (not isinstance(decision, dict) or set(decision) != {'decision', 'evidence'} or
                    decision['decision'] != 'confirmed' or not isinstance(decision['evidence'], str) or
                    not re.fullmatch(r'[\w .,/()–-]{3,500}', decision['evidence'])):
                raise ValueError
    except (ValueError, KeyError, TypeError):
        raise DetailImportError('Archivfreigabe verweigert: offene Befunde oder ungültiger Prüfbeleg.') from None
