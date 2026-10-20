"""Seitenaufrufe lesen nur lokale Daten und lösen keine Importe aus."""
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
    weeks = sorted({event["week"] for event in data["events"]}) if data else []
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
                                             days=days, previous=previous, following=following))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
