"""Kalenderaufbereitung für die lokale, unvollständige Vorschau."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

DAY_NAMES = ('Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag')


def default_week(weeks, today=None):
    if not weeks:
        return ''
    today = today or datetime.now(ZoneInfo('Europe/Berlin')).date()
    year, week, _ = today.isocalendar()
    current = f'{year}-W{week:02d}'
    return next((value for value in weeks if value >= current), weeks[-1])


def week_days(week, events):
    year, number = week.split('-W')
    monday = date.fromisocalendar(int(year), int(number), 1)
    days = [{'name': name, 'date': (monday + timedelta(days=index)).strftime('%d.%m.%Y'), 'events': []}
            for index, name in enumerate(DAY_NAMES)]
    for event in sorted(events, key=lambda item: (datetime.fromisoformat(item['start']), item['title'])):
        local = datetime.fromisoformat(event['start']).astimezone(ZoneInfo('Europe/Berlin'))
        if monday <= local.date() <= monday + timedelta(days=6):
            days[local.weekday()]['events'].append(event)
    return days
