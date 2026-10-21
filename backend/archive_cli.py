"""Manueller Kalenderimport und lokale Archivverwaltung; keine HTTP-Schreibendpunkte."""
import json
import os
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext

from backend.importer.calendar import run_calendar_import
from backend.importer.calendar_policy import parse_policy
from backend.importer.comparison import ComparisonInputError
from backend.importer.details import DetailImportError
from backend.importer.http import SourceClient, SourceFetchError
from backend.importer.identity import configured_identity, SourceIdentityError
from backend.storage.archive import (LIMIT, begin_run, fail_run, stage_run, import_lock,
                                     get_candidate, publish_run, history, backup_archive)


def read_json(filename):
    try:
        with open(filename, 'rb') as stream:
            raw = stream.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result
        return json.loads(raw, object_pairs_hook=unique_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
    except (OSError, ValueError, TypeError):
        raise DetailImportError('Lokale JSON-Datei ist nicht lesbar, zu groß oder ungültig.') from None


def _database():
    value = current_app.config.get('ARCHIVE_DATABASE', '')
    if not value:
        raise DetailImportError('ARCHIVE_DATABASE als absoluten Datenpfad konfigurieren.')
    return value


def _error(error):
    raise click.ClickException(str(error)) from None


@click.command('source-calendar-import')
@click.option('--query', envvar='LSF_STUDY_QUERY', required=True)
@click.option('--policy', required=True, type=click.Path(dir_okay=False))
@click.option('--detail-budget', default=80, type=click.IntRange(1, 100))
@with_appcontext
def calendar_import(query, policy, detail_budget):
    """Gesamtes Semester prüfen und einen unveröffentlichten Archivlauf speichern."""
    try:
        rules = parse_policy(read_json(policy))
        database = _database()
        identity = configured_identity(current_app.config.get('LSF_ID_PARAMETER', ''),
                                       current_app.config.get('LSF_ID_NAMESPACE', ''))
        with import_lock(database), SourceClient(current_app.config.get('LSF_BASE_URL', ''),
                                                max_requests=100, retries=0) as client:
            run_id = begin_run(database, rules.to_dict())
            try:
                candidate = run_calendar_import(client, query=query, policy=rules,
                                                identity_policy=identity, detail_budget=detail_budget)
                stage_run(database, run_id, candidate)
            except BaseException:
                fail_run(database, run_id)
                raise
        report = {'run_id': run_id, 'status': 'provisional', 'candidate_digest': candidate['digest'],
                  'event_count': len(candidate['events']), 'suppressed_count': len(candidate['suppressed']),
                  'hard_blocker_count': len(candidate['hard_blockers']),
                  'review_count': len(candidate['reviews']), 'complete': False, 'published': False}
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    except (DetailImportError, SourceFetchError, SourceIdentityError, ComparisonInputError) as error:
        _error(error)
    raise click.exceptions.Exit(1)


@click.command('archive-review-export')
@click.option('--run-id', required=True)
@click.option('--output', required=True, type=click.Path(dir_okay=False))
@with_appcontext
def review_export(run_id, output):
    """Prüfpaket mit Originalhinweisen und unbestätigter Entscheidungsvorlage exportieren."""
    created = False
    try:
        candidate = get_candidate(_database(), run_id)
        target = Path(output)
        repository = Path(__file__).resolve().parent.parent
        if not target.is_absolute() or target.resolve().is_relative_to(repository):
            raise DetailImportError('Prüfpaket außerhalb des Repositorys als absoluten Datenpfad ablegen.')
        packet = {'candidate': candidate,
                  'approval': {'schema': 1, 'candidate_digest': candidate['digest'],
                               'decisions': {r['id']: {'decision': 'pending', 'evidence': ''}
                                             for r in candidate['reviews']}}}
        with open(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'w') as stream:
            created = True
            json.dump(packet, stream, ensure_ascii=False, indent=2)
        click.echo('Prüfpaket mit Dateirechten 0600 exportiert. Fachliche Befunde einzeln prüfen.')
    except (OSError, ValueError):
        if created:
            target.unlink(missing_ok=True)
        _error(DetailImportError('Prüfpaket nicht geschrieben; neues Ziel und Datenrechte prüfen.'))
    except DetailImportError as error:
        _error(error)


@click.command('archive-publish')
@click.option('--run-id', required=True)
@click.option('--review', required=True, type=click.Path(dir_okay=False))
@with_appcontext
def archive_publish(run_id, review):
    """Geprüften vorläufigen Stand transaktional veröffentlichen; ohne Quellzugriff."""
    try:
        packet = read_json(review)
        if not isinstance(packet, dict) or not isinstance(packet.get('approval'), dict):
            raise DetailImportError('Freigabepaket enthält keinen gültigen Prüfbeleg.')
        database = _database()
        if packet.get('candidate') != get_candidate(database, run_id):
            raise DetailImportError('Prüfpaket stimmt nicht mit dem gespeicherten Importinhalt überein.')
        result = publish_run(database, run_id, packet['approval'])
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    except DetailImportError as error:
        _error(error)


@click.command('archive-history')
@with_appcontext
def archive_history():
    """Importläufe und Fehlversuche ohne vertrauliche Quellinhalte anzeigen."""
    try:
        click.echo(json.dumps(history(_database()), ensure_ascii=False, indent=2))
    except DetailImportError as error:
        _error(error)


@click.command('archive-backup')
@click.option('--output', required=True, type=click.Path(dir_okay=False))
@with_appcontext
def archive_backup(output):
    """Konsistente SQLite-Sicherung in eine neue Datei schreiben und prüfen."""
    try:
        backup_archive(_database(), output)
        click.echo('Archivsicherung erstellt und auf Integrität geprüft.')
    except DetailImportError as error:
        _error(error)


@click.command('archive-restore')
@click.option('--input', 'source', required=True, type=click.Path(dir_okay=False))
@click.option('--output', required=True, type=click.Path(dir_okay=False))
@with_appcontext
def archive_restore(source, output):
    """Sicherung geprüft in eine neue Datei wiederherstellen; niemals aktives Archiv ersetzen."""
    try:
        backup_archive(source, output)
        click.echo('Archiv in neue Datei wiederhergestellt und auf Integrität geprüft.')
    except DetailImportError as error:
        _error(error)


def register_archive_cli(app):
    for command in (calendar_import, review_export, archive_publish, archive_history, archive_backup, archive_restore):
        app.cli.add_command(command)
