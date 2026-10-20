"""Separate, explicitly incomplete preview; never an archive snapshot."""
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.importer.details import DetailImportError

LIMIT = 5_000_000


def validate_preview(data):
    if not isinstance(data, dict) or data.get("schema") != 1 or data.get("complete") is not False:
        raise ValueError("Invalid preview")
    for name in ("semester", "created_at"):
        if not isinstance(data.get(name), str) or len(data[name]) > 200:
            raise ValueError("Invalid metadata")
    stamp = datetime.fromisoformat(data["created_at"])
    if stamp.tzinfo is None:
        raise ValueError("Missing timezone")
    for name in ("blocked_details", "checked_details"):
        if type(data.get(name)) is not int or not 0 <= data[name] <= 100:
            raise ValueError("Invalid counts")
    if data["blocked_details"] > data["checked_details"]:
        raise ValueError("Invalid counts")
    events = data.get("events")
    if not isinstance(events, list) or not 0 < len(events) <= 20000:
        raise ValueError("Invalid events")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Invalid event")
        for key in ("title", "room", "instructor"):
            if not isinstance(event.get(key), str) or len(event[key]) > 1000:
                raise ValueError("Invalid text")
        start, end = (datetime.fromisoformat(event[key]) for key in ("start", "end"))
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError("Invalid time")
        if type(event.get("review")) is not bool:
            raise ValueError("Invalid review flag")
    return data


def save_preview_file(filename, sample, semester):
    """Replace only after a complete bounded fetch; preserve old preview on failure."""
    temporary = None
    try:
        if sample.unchecked_count or not sample.details:
            raise ValueError("Partial fetch")
        events = []
        for detail in sample.details:
            if detail.preview is None:
                continue
            for event in detail.preview.occurrences:
                events.append({"title": detail.preview.title, "start": event.starts_at,
                               "end": event.ends_at, "room": event.room or "",
                               "instructor": event.instructor or "", "review": detail.requires_review})
        data = validate_preview({"schema": 1, "complete": False, "semester": semester,
                                 "created_at": datetime.now(timezone.utc).isoformat(),
                                 "checked_details": len(sample.details),
                                 "blocked_details": sum(d.preview is None for d in sample.details),
                                 "events": sorted(events, key=lambda e: (e["start"], e["title"]))})
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        if len(payload) > LIMIT:
            raise ValueError("Too large")
        target = Path(filename)
        if not target.is_absolute():
            raise ValueError("Absolute path required")
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".preview-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except (OSError, ValueError, TypeError, KeyError):
        raise DetailImportError("Vorschau nicht gespeichert; bisherigen Stand beibehalten. Datenpfad und Rechte prüfen.") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_preview_file(filename):
    if not filename:
        return None, "disabled"
    try:
        with open(filename, "rb") as stream:
            raw = stream.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError("Too large")
        data = validate_preview(json.loads(raw))
        zone = ZoneInfo("Europe/Berlin")
        for event in data["events"]:
            start, end = (datetime.fromisoformat(event[key]).astimezone(zone) for key in ("start", "end"))
            event.update(day=start.strftime("%d.%m.%Y"), time=start.strftime("%H:%M") + "–" + end.strftime("%H:%M"),
                         week=f"{start.isocalendar().year}-W{start.isocalendar().week:02d}")
        data["created_label"] = datetime.fromisoformat(data["created_at"]).astimezone(zone).strftime("%d.%m.%Y %H:%M")
        return data, "ready"
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return None, "invalid"
