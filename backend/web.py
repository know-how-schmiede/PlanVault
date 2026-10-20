"""Seitenaufrufe lesen nur lokale Daten und lösen keine Importe aus."""
from flask import Blueprint, render_template, current_app, request, make_response
from backend.preview import load_preview_file

web = Blueprint("web", __name__)


@web.get("/")
def index():
    return render_template("index.html")


@web.get("/vorschau")
def preview():
    data, status = load_preview_file(current_app.config.get("PREVIEW_FILE", ""))
    weeks = sorted({event["week"] for event in data["events"]}) if data else []
    selected = request.args.get("week", "")
    if selected and selected not in weeks:
        return "Unbekannte Kalenderwoche.", 400
    events = [event for event in data["events"] if not selected or event["week"] == selected] if data else []
    response = make_response(render_template("preview.html", preview=data, status=status,
                                             weeks=weeks, selected=selected, events=events))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
