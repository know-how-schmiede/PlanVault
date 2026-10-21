"""Seitenaufrufe lesen nur lokale Daten und lösen keine Importe aus."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from backend.storage.archive import read_snapshot
from backend.importer.details import DetailImportError
from flask import Blueprint, render_template, current_app, request, make_response
from backend.preview import load_preview_file
from backend.preview_calendar import default_week, week_days

web = Blueprint("web", __name__)


@web.get("/")
def index():
    return render_template("index.html")


@web.get("/vorschau")
def preview():
    mode = request.args.get("view", "week")
    if mode not in {"week", "list"}:
        return "Unbekannte Ansicht.", 400
    data, status = load_preview_file(current_app.config.get("PREVIEW_FILE", ""))
    return _calendar_response(data, status)


@web.get('/archiv')
def archive():
    filename = current_app.config.get('ARCHIVE_DATABASE', '')
    if not filename:
        return _calendar_response(None, 'disabled', archived=True)
    selected = request.args.get('snapshot')
    if selected is not None and (len(selected) > 19 or not selected.isascii() or not selected.isdigit() or not 1 <= int(selected) <= 2**63-1):
        return 'Ungültiger Archivstand.', 400
    try:
        data = read_snapshot(filename, int(selected) if selected else None)
        if data:
            zone = ZoneInfo('Europe/Berlin')
            data.update(semester=data['policy']['semester'], study_title=data['policy']['study_title'])
            for event in data['events']:
                start, end = (datetime.fromisoformat(event[k]).astimezone(zone) for k in ('start', 'end'))
                event.update(day=start.strftime('%d.%m.%Y'), time=start.strftime('%H:%M')+'–'+end.strftime('%H:%M'),
                             week=f'{start.isocalendar().year}-W{start.isocalendar().week:02d}')
            for field in ('created_at', 'last_success_at', 'last_attempt_at'):
                data[field+'_label'] = datetime.fromisoformat(data[field]).astimezone(zone).strftime('%d.%m.%Y %H:%M') if data[field] else 'unbekannt'
        return _calendar_response(data, 'ready' if data else 'missing', archived=True)
    except DetailImportError:
        return _calendar_response(None, 'invalid', archived=True)


def _calendar_response(data, status, archived=False):
    mode = request.args.get('view', 'week')
    if mode not in {'week', 'list'}:
        return 'Unbekannte Ansicht.', 400
    weeks = sorted({event["week"] for event in data["events"]}) if data else []
    if archived and data:
        first, last = (date.fromisoformat(data['policy'][key]) for key in ('start', 'end'))
        monday = first - timedelta(days=first.weekday())
        weeks = []
        while monday <= last:
            weeks.append(f'{monday.isocalendar().year}-W{monday.isocalendar().week:02d}')
            monday += timedelta(days=7)
    selected = request.args.get("week", "")
    if selected and selected not in weeks:
        return "Unbekannte Kalenderwoche.", 400
    if mode == "week" and not selected:
        selected = default_week(weeks)
    events = [event for event in data["events"] if not selected or event["week"] == selected] if data else []
    days = week_days(selected, events) if selected and mode == "week" else []
    position = weeks.index(selected) if selected else None
    previous = weeks[position - 1] if position is not None and position > 0 else None
    following = weeks[position + 1] if position is not None and position + 1 < len(weeks) else None
    response = make_response(render_template("preview.html", preview=data, status=status,
                                             weeks=weeks, selected=selected, events=events, mode=mode,
                                             days=days, previous=previous, following=following,
                                             archived=archived, calendar_endpoint="web.archive" if archived else "web.preview"))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
