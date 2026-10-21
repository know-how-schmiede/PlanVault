"""Wochenpräsenz normalisierter Termine; keine Prüfung von Uhrzeit oder Raum."""

from datetime import date, timedelta

from backend.importer.details import DetailSample, DetailImportError, fetch_detail_sample
from backend.importer.semester import validate_semester_details
from backend.importer.notices import DayNotice, KNOWN_NOTICE_KINDS


NOTICE_ASSESSMENTS = (
    'all_expected_dates_with_known_notice', 'some_expected_dates_with_known_notice',
    'unclassified_notice_on_expected_date', 'no_notice_on_expected_dates',
    'day_notice_evidence_unavailable',
)


def assess_notice_context(expected_dates, notices):
    if notices is None:
        return 'day_notice_evidence_unavailable', []
    matching = [n for n in notices if n.local_date in expected_dates]
    known = {n.local_date for n in matching if n.kind in KNOWN_NOTICE_KINDS}
    if known and known == expected_dates:
        assessment = 'all_expected_dates_with_known_notice'
    elif known:
        assessment = 'some_expected_dates_with_known_notice'
    elif matching:
        assessment = 'unclassified_notice_on_expected_date'
    else:
        assessment = 'no_notice_on_expected_dates'
    return assessment, [{'local_date': n.local_date, 'kind': n.kind}
                        for n in sorted(matching, key=lambda n: n.local_date)]


def fetch_comparison_details(client, references, *, semester, study_key, regulations_key, budget):
    validate_semester_details(semester, study_key, regulations_key, budget)
    if not references or len(references) > budget:
        raise DetailImportError("Keine Detailziele oder Detailbudget überschritten.")
    if (len({r.key for r in references}) != len(references) or
            len({r.location for r in references}) != len(references)):
        raise DetailImportError("Doppelte Detailauswahl für den Terminabgleich.")
    if any(r.identity_scope != 'configured' for r in references):
        raise DetailImportError("Terminabgleich benötigt konfigurierte Veranstaltungskennungen.")
    details = []
    for reference in references:
        sample = fetch_detail_sample(client, (reference,), semester=semester, study_key=study_key,
                                     regulations_key=regulations_key, limit=1)
        details.extend(sample.details)
    return DetailSample(len(references), sum(r.block_count for r in references), tuple(details))


def compare_weekly_presence(references, sample, week_references, week_statuses, *, start, end,
                            day_notices=None):
    """Veranstaltung pro voller beobachteter Woche vergleichen; keine Vollständigkeitsfreigabe.

    Mehrere Termine derselben Veranstaltung bilden eine Wochenpräsenz. Wochenende,
    Randwochen, blockierte Details und nicht beobachtete Wochen bleiben separat.
    """
    keys = tuple(r.key for r in references)
    if (len(set(keys)) != len(keys) or sample.unchecked_count or
            tuple(d.reference_key for d in sample.details) != keys or
            set(week_references) != set(week_statuses) or
            any(status not in {'ok', 'empty_unverified', 'notes_require_review'}
                for status in week_statuses.values()) or
            any(key not in set(keys) for refs in week_references.values() for key in refs)):
        raise DetailImportError("Unvollständige oder widersprüchliche Grundlage für den Terminabgleich.")
    notices_by_week = {} if day_notices is None else day_notices
    if set(notices_by_week) - set(week_references):
        raise DetailImportError("Tageshinweise gehören nicht zu beobachteten Wochen.")
    for week, notices in notices_by_week.items():
        if (any(not isinstance(n, DayNotice) for n in notices) or
                len({n.local_date for n in notices}) != len(notices) or
                any(date.fromisoformat(n.local_date).isocalendar()[:2] != week or
                    date.fromisoformat(n.local_date).weekday() >= 5 for n in notices)):
            raise DetailImportError("Tageshinweise sind widersprüchlich oder gehören nicht zur Woche.")
    full_weeks = {week for week in week_references
                  if start <= date.fromisocalendar(*week, 1) and
                  date.fromisocalendar(*week, 1) + timedelta(days=6) <= end}
    numbers = {key: number for number, key in enumerate(keys, 1)}
    missing, unexpected, cancelled_visible, weekend_visible = [], [], [], []
    blocked, review, unobserved = [], [], set()
    matched, expected_count, observed_count, weekend_count = 0, 0, 0, 0
    normalizable = 0
    notice_counts = {kind: 0 for kind in NOTICE_ASSESSMENTS}
    week_counts = {week: {'iso_year': week[0], 'iso_week': week[1],
                          'week_status': week_statuses[week], 'expected_course_weeks': 0,
                          'observed_course_weeks': 0, 'matched_course_weeks': 0,
                          'missing_count': 0, 'unexpected_count': 0,
                          'cancellation_only_count': 0, 'weekend_only_count': 0,
                          'missing_notice_context_counts': {kind: 0 for kind in NOTICE_ASSESSMENTS}}
                   for week in sorted(full_weeks)}
    for detail in sample.details:
        number = numbers[detail.reference_key]
        if detail.preview is None:
            blocked.append(number)
            continue
        normalizable += 1
        if detail.requires_review:
            review.append(number)
        expected, cancelled, weekend = set(), set(), set()
        expected_dates = {}
        for occurrence in detail.preview.occurrences:
            day = date.fromisoformat(occurrence.local_date)
            if not start <= day <= end:
                continue
            week = tuple(day.isocalendar()[:2])
            if day.weekday() >= 5:
                weekend_count += 1
                weekend.add(week)
            else:
                expected.add(week)
                expected_dates.setdefault(week, set()).add(day.isoformat())
        for cancellation in detail.preview.cancellations:
            day = date.fromisoformat(cancellation.local_date)
            if start <= day <= end and day.weekday() < 5:
                cancelled.add(tuple(day.isocalendar()[:2]))
        unobserved.update(expected - set(week_references))
        for week in sorted(full_weeks):
            visible = detail.reference_key in week_references[week]
            planned = week in expected
            expected_count += int(planned)
            observed_count += int(visible)
            counts = week_counts[week]
            counts['expected_course_weeks'] += int(planned)
            counts['observed_course_weeks'] += int(visible)
            row = {'detail_number': number, 'iso_year': week[0], 'iso_week': week[1],
                   'week_status': week_statuses[week], 'detail_requires_review': detail.requires_review}
            if visible and planned:
                matched += 1
                counts['matched_course_weeks'] += 1
            elif planned:
                dates = expected_dates[week]
                assessment, matching_notices = assess_notice_context(dates, notices_by_week.get(week))
                row.update(expected_local_dates=sorted(dates), notice_assessment=assessment,
                           expected_day_notices=matching_notices)
                missing.append(row)
                counts['missing_count'] += 1
                counts['missing_notice_context_counts'][assessment] += 1
                notice_counts[assessment] += 1
            elif visible:
                if week in cancelled:
                    cancelled_visible.append(row)
                    counts['cancellation_only_count'] += 1
                elif week in weekend:
                    weekend_visible.append(row)
                    counts['weekend_only_count'] += 1
                else:
                    unexpected.append(row)
                    counts['unexpected_count'] += 1
    evaluated = bool(full_weeks) and normalizable > 0
    return {
        'scope': 'course_presence_per_full_observed_week', 'evaluated': evaluated,
        'compared_weeks': sorted(full_weeks), 'weeks': list(week_counts.values()),
        'partial_boundary_weeks': sorted(set(week_references) - full_weeks),
        'unobserved_expected_weeks': sorted(unobserved),
        'normalizable_details': normalizable, 'blocked_details': blocked, 'review_details': review,
        'expected_course_weeks': expected_count, 'observed_course_weeks': observed_count,
        'matched_course_weeks': matched, 'missing_from_week_view': missing,
        'missing_notice_context_counts': notice_counts,
        'day_notice_policy': 'context_only_no_automatic_exclusion',
        'observed_without_expected_occurrence': unexpected,
        'observed_cancellation_only': cancelled_visible, 'observed_weekend_only': weekend_visible,
        'weekend_occurrence_count': weekend_count,
        'comparable_pairs_match': not (missing or unexpected) if evaluated else None,
        'complete': False,
    }
