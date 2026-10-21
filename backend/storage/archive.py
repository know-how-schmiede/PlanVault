"""SQLite-Archiv: vorläufige Läufe, atomare Freigabe, unveränderliche Snapshots."""
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from backend.importer.calendar import validate_review
from backend.importer.calendar_policy import digest
from backend.importer.details import DetailImportError

LIMIT = 20_000_000


def _now():
    return datetime.now(timezone.utc).isoformat()


def scope_for(policy):
    return digest({key: policy[key] for key in ('semester', 'study_key', 'regulations_key', 'start', 'end')})


def _path(filename):
    target = Path(filename)
    if not filename or not target.is_absolute() or target.is_symlink():
        raise DetailImportError('Absoluten lokalen Archivpfad ohne symbolischen Link konfigurieren.')
    return target


@contextmanager
def import_lock(filename):
    """Ein Import pro Archivdatei; keine Langzeittransaktion während HTTP-Abrufen."""
    target = _path(filename)
    try:
        fd = os.open(str(target) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise DetailImportError('Für dieses Archiv läuft bereits ein Import.') from None
            yield
    except OSError:
        raise DetailImportError('Archivsperre konnte nicht eingerichtet werden.') from None


@contextmanager
def connect(filename):
    target = _path(filename)
    connection = None
    try:
        try:
            fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        except FileExistsError:
            pass
        connection = sqlite3.connect(target, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA synchronous=FULL')
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version == 0:
            if connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                raise DetailImportError('Unbekanntes Archivschema; keine automatische Änderung.')
            connection.executescript('''
                BEGIN IMMEDIATE;
                CREATE TABLE runs(id TEXT PRIMARY KEY, scope TEXT NOT NULL, started_at TEXT NOT NULL,
                    finished_at TEXT, status TEXT NOT NULL, error_code TEXT, candidate TEXT, approval TEXT);
                CREATE TABLE snapshots(id INTEGER PRIMARY KEY, scope TEXT NOT NULL, content_hash TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs(id),
                    UNIQUE(scope, content_hash));
                CREATE TABLE heads(scope TEXT PRIMARY KEY, snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
                    last_success_at TEXT NOT NULL);
                PRAGMA user_version=1;
                COMMIT;
            ''')
        elif version != 1:
            raise DetailImportError('Nicht unterstützte Archivversion; Migration erforderlich.')
        yield connection
    except (sqlite3.Error, OSError, ValueError):
        raise DetailImportError('Archivzugriff fehlgeschlagen; bisherigen Stand beibehalten.') from None
    finally:
        if connection is not None:
            connection.close()


def begin_run(filename, policy):
    run_id = str(uuid4())
    with connect(filename) as db, db:
        db.execute('INSERT INTO runs(id,scope,started_at,status) VALUES(?,?,?,?)',
                   (run_id, scope_for(policy), _now(), 'running'))
    return run_id


def fail_run(filename, run_id):
    with connect(filename) as db, db:
        db.execute("UPDATE runs SET status='failed',finished_at=?,error_code='import_failed' WHERE id=? AND status='running'",
                   (_now(), run_id))


def stage_run(filename, run_id, candidate):
    raw = json.dumps(candidate, ensure_ascii=False, allow_nan=False)
    if len(raw.encode()) > LIMIT or candidate['digest'] != digest({k:v for k,v in candidate.items() if k != 'digest'}):
        raise DetailImportError('Vorläufiger Importinhalt ist ungültig oder zu groß.')
    with connect(filename) as db, db:
        changed = db.execute("UPDATE runs SET status='provisional',finished_at=?,candidate=? WHERE id=? AND scope=? AND status='running'",
                             (_now(), raw, run_id, scope_for(candidate['policy']))).rowcount
        if changed != 1:
            raise DetailImportError('Importlauf passt nicht zum vorläufigen Archivstand.')


def get_candidate(filename, run_id):
    with connect(filename) as db:
        row = db.execute('SELECT candidate FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None or not row['candidate']:
            raise DetailImportError('Kein vorläufiger Inhalt für diesen Importlauf.')
        return json.loads(row['candidate'])


def publish_run(filename, run_id, approval):
    with connect(filename) as db, db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None or row['status'] != 'provisional':
            raise DetailImportError('Nur ein vorläufiger Importlauf kann freigegeben werden.')
        candidate = json.loads(row['candidate'])
        validate_review(candidate, approval)
        payload = {'schema': 1, 'complete': True, 'policy': candidate['policy'], 'events': candidate['events']}
        fingerprint = digest(payload)
        previous = db.execute('SELECT id FROM snapshots WHERE scope=? AND content_hash=?',
                              (row['scope'], fingerprint)).fetchone()
        stamp = _now()
        if previous is None:
            cursor = db.execute('INSERT INTO snapshots(scope,content_hash,payload,created_at,run_id) VALUES(?,?,?,?,?)',
                                (row['scope'], fingerprint, json.dumps(payload, ensure_ascii=False), stamp, run_id))
            snapshot_id = cursor.lastrowid
        else:
            snapshot_id = previous['id']
        db.execute('INSERT INTO heads VALUES(?,?,?) ON CONFLICT(scope) DO UPDATE SET snapshot_id=excluded.snapshot_id,last_success_at=excluded.last_success_at',
                   (row['scope'], snapshot_id, stamp))
        status = 'published' if previous is None else 'unchanged'
        db.execute('UPDATE runs SET status=?,finished_at=?,approval=? WHERE id=?',
                   (status, stamp, json.dumps(approval, ensure_ascii=False), run_id))
        return {'run_id': run_id, 'snapshot_id': snapshot_id, 'status': status, 'published': True}


def history(filename):
    with connect(filename) as db:
        return [dict(row) for row in db.execute('SELECT id,scope,started_at,finished_at,status,error_code FROM runs ORDER BY started_at DESC LIMIT 200')]


def read_snapshot(filename, snapshot_id=None, scope=None):
    """Nur lesend öffnen: Webseiten legen weder Schema noch Datenbank an."""
    target = _path(filename)
    db = None
    try:
        db = sqlite3.connect(target.as_uri() + '?mode=ro', uri=True, timeout=5)
        db.row_factory = sqlite3.Row
        if db.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError
        if snapshot_id is None:
            rows = db.execute('SELECT s.*,h.last_success_at FROM heads h JOIN snapshots s ON h.snapshot_id=s.id WHERE (? IS NULL OR h.scope=?) ORDER BY h.last_success_at DESC', (scope,scope)).fetchall()
            row = rows[0] if rows else None
        else:
            row = db.execute('SELECT s.*,h.last_success_at FROM snapshots s LEFT JOIN heads h ON h.scope=s.scope WHERE s.id=?', (snapshot_id,)).fetchone()
        if row is None:
            return None
        payload = json.loads(row['payload'])
        if payload.get('complete') is not True or digest(payload) != row['content_hash']:
            raise ValueError
        latest = db.execute('SELECT status,started_at FROM runs WHERE scope=? ORDER BY started_at DESC LIMIT 1', (row['scope'],)).fetchone()
        payload.update(snapshot_id=row['id'], created_at=row['created_at'], last_success_at=row['last_success_at'],
                       last_attempt_status=latest['status'] if latest else None,
                       last_attempt_at=latest['started_at'] if latest else None)
        return payload
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
        raise DetailImportError('Archivstand ist nicht lesbar oder beschädigt.') from None
    finally:
        if db is not None:
            db.close()


def backup_archive(filename, destination):
    target = _path(destination)
    if target.exists():
        raise DetailImportError('Sicherungsziel existiert bereits.')
    created = False
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        created = True
        source_path = _path(filename)
        with closing(sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(target)) as backup:
            if source.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise DetailImportError('Nicht unterstütztes Schema der Archivsicherung.')
            source.backup(backup)
            if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or backup.execute('PRAGMA foreign_key_check').fetchall():
                raise DetailImportError('Integritätsprüfung der Archivsicherung fehlgeschlagen.')
    except (OSError, sqlite3.Error, DetailImportError):
        if created:
            target.unlink(missing_ok=True)
        raise DetailImportError('Archivsicherung fehlgeschlagen.') from None
