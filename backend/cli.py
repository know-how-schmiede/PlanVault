"""Manuelle Diagnose; kein Quellzugriff durch normale Webseitenaufrufe."""

import re
from datetime import date

import click
from bs4 import BeautifulSoup
from flask import current_app
from flask.cli import with_appcontext

from backend.importer.http import SourceClient, SourceFetchError
from backend.importer.forms import FormNavigationError
from backend.importer.navigation import search_study, follow_named_result, submit_labeled_search
from backend.importer.weeks import audit_weeks
from backend.importer.weeks import read_week_menu, inspect_week
from backend.importer.details import collect_course_references, fetch_detail_sample, DetailImportError


@click.command("source-check")
@with_appcontext
def source_check():
    """Konfigurierte Einstiegsseite einmal prüfen, ohne Adressen auszugeben."""
    base_url = current_app.config.get("LSF_BASE_URL", "")
    try:
        with SourceClient(base_url, max_requests=5, retries=0) as client:
            document = client.fetch()
        soup = BeautifulSoup(document.html, "html.parser")
        if soup.find("input", attrs={"type": re.compile("^password$", re.I)}):
            raise SourceFetchError("Anmeldeseite erkannt; Zugang muss geprüft werden.")
        if not soup.find("form") or not soup.find("select"):
            raise SourceFetchError("Erwartete Formularstruktur fehlt; Quelle manuell prüfen.")
    except SourceFetchError as error:
        raise click.ClickException(str(error)) from None
    click.echo("Einstiegsseite erreichbar; Formular und Auswahlfelder erkannt.")
    click.echo("Kein Import durchgeführt. Studiengang, Semester und Vollständigkeit sind noch ungeprüft.")


@click.command("source-plan-check")
@click.option("--query", required=True, help="Kurzer Suchtext für den Studiengang.")
@click.option("--title", required=True, help="Exakte Trefferbeschriftung einschließlich Prüfungsordnung.")
@with_appcontext
def source_plan_check(query, title):
    """Studiengangsnavigation prüfen; keinen Archivstand veröffentlichen."""
    try:
        with SourceClient(current_app.config.get("LSF_BASE_URL", ""), max_requests=10, retries=0) as client:
            results = search_study(client, query)
            selection = follow_named_result(client, results, title=title)
            plan = submit_labeled_search(client, selection, field_label="Studiengang",
                                         button_caption="Suche starten")
        soup = BeautifulSoup(plan.html, "html.parser")
        if soup.select('input[type="password" i]'):
            raise FormNavigationError("Anmeldeseite statt Planantwort erhalten.")
        count = len(soup.select("td.plan5a"))
        if not count:
            raise FormNavigationError("Kein bekanntes Veranstaltungsmuster erkannt; keine bestätigte leere Planung.")
    except (SourceFetchError, FormNavigationError) as error:
        raise click.ClickException(str(error)) from None
    click.echo(f"Studiengangsnavigation erfolgreich; {count} bekannte Veranstaltungsblöcke erkannt.")
    click.echo("Kein Import oder Archivstand erstellt. Semester, Filter und Vollständigkeit bleiben zu prüfen.")


@click.command("source-weeks-check")
@click.option("--query", required=True)
@click.option("--title", required=True)
@click.option("--start", required=True, type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--end", required=True, type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--week", "weeks", multiple=True, required=True, help="Explizite ISO-Woche, z. B. 2026-W44; wiederholbar.")
@with_appcontext
def source_weeks_check(query, title, start, end, weeks):
    """Ausgewählte Wochen gegen einen unabhängig angegebenen Zeitraum prüfen."""
    requested = []
    try:
        for value in weeks:
            match = re.fullmatch(r"(\d{4})-W(\d{2})", value)
            if not match:
                raise ValueError
            key = int(match[1]), int(match[2])
            date.fromisocalendar(*key, 1)
            requested.append(key)
        if (not 0 <= (end - start).days <= 370 or
                len(requested) > 54 or len(set(requested)) != len(requested)):
            raise ValueError
    except ValueError:
        raise click.ClickException("Ungültiger Zeitraum oder doppelte/ungültige ISO-Wochen.") from None
    try:
        with SourceClient(current_app.config.get("LSF_BASE_URL", ""),
                          max_requests=min(100, 10 + 2 * len(requested)), retries=0) as client:
            results = search_study(client, query)
            selection = follow_named_result(client, results, title=title)
            plan = submit_labeled_search(client, selection, field_label="Studiengang", button_caption="Suche starten")
            audit = audit_weeks(client, plan, start=start.date(), end=end.date(), requested=tuple(requested))
    except (SourceFetchError, FormNavigationError) as error:
        raise click.ClickException(str(error)) from None
    statuses = {"ok": "Wochenstruktur erkannt", "empty_unverified": "Leere Ansicht ungeprüft",
                "notes_require_review": "Tageshinweise benötigen Prüfung", "failed": "Abruf oder Strukturprüfung fehlgeschlagen"}
    for result in audit.results:
        click.echo(f"{result.iso_year}-W{result.iso_week:02d}: {statuses[result.status]}")
    click.echo(f"Fehlende Wochen: {len(audit.coverage.missing)}; ungeklärte/fehlerhafte Wochen: {len(audit.coverage.failed)}.")
    click.echo("Kein Semesterimport oder Archivstand erstellt; Veranstaltungs-Vollständigkeit ist nicht bestätigt.")
    if not audit.coverage.weeks_complete:
        raise click.ClickException("Wochenprüfung ist unvollständig.")


@click.command("source-details-check")
@click.option("--query", required=True)
@click.option("--title", required=True)
@click.option("--semester", required=True, help="Erwartete Semesterbeschriftung der Detailseite.")
@click.option("--study-key", required=True, help="Lokale opake Studiengangskennung.")
@click.option("--regulations-key", required=True, help="Lokale opake Prüfungsordnungskennung.")
@click.option("--week", required=True, help="Explizite ISO-Woche, z. B. 2026-W44.")
@click.option("--limit", default=2, show_default=True, type=click.IntRange(1, 10))
@with_appcontext
def source_details_check(query, title, semester, study_key, regulations_key, week, limit):
    """Kleine Detailstichprobe aus einer ausdrücklich gewählten Woche prüfen."""
    try:
        match = re.fullmatch(r"(\d{4})-W(\d{2})", week)
        if not match:
            raise ValueError
        key = int(match[1]), int(match[2])
        date.fromisocalendar(*key, 1)
        if not semester.strip() or any(not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value)
                                       for value in (study_key, regulations_key)):
            raise ValueError
    except ValueError:
        raise click.ClickException("ISO-Woche, Semester oder lokale Kennungen ungültig.") from None
    try:
        with SourceClient(current_app.config.get("LSF_BASE_URL", ""), max_requests=12 + limit, retries=0) as client:
            results = search_study(client, query)
            selection = follow_named_result(client, results, title=title)
            plan = submit_labeled_search(client, selection, field_label="Studiengang", button_caption="Suche starten")
            menu = read_week_menu(plan)
            choices = [choice for choice in menu.choices if choice.key == key]
            if len(choices) != 1:
                raise DetailImportError("Gewünschte Woche wird nicht angeboten.")
            plan = menu.form.submit(client, values={menu.field_name: (choices[0].value,)}, button=menu.button)
            if inspect_week(plan, choices[0]).status != "ok":
                raise DetailImportError("Woche ist leer oder prüfpflichtig; keine Detailstichprobe gestartet.")
            references = collect_course_references(client, (plan,))
            sample = fetch_detail_sample(client, references, semester=semester, study_key=study_key,
                                         regulations_key=regulations_key, limit=limit)
    except (DetailImportError, FormNavigationError, SourceFetchError) as error:
        raise click.ClickException(str(error)) from None
    click.echo(f"Veranstaltungsblöcke: {sample.block_count}; eindeutige Detailziele: {sample.reference_count}.")
    click.echo(f"Geprüfte Details: {len(sample.details)}; ungeprüfte Detailziele: {sample.unchecked_count}.")
    review = sum(result.status != "preview" for result in sample.details)
    click.echo(f"Details mit ungeklärter Normalisierung: {review}.")
    click.echo("Nur Stichprobe: keine dauerhafte Quellidentität, kein vollständiger Semesterimport, kein Archivstand.")
    if review:
        raise click.ClickException("Detailnormalisierung benötigt Prüfung.")


def register_cli(app):
    app.cli.add_command(source_check)
    app.cli.add_command(source_plan_check)
    app.cli.add_command(source_weeks_check)
    app.cli.add_command(source_details_check)
