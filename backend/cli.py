"""Manuelle Diagnose; kein Quellzugriff durch normale Webseitenaufrufe."""

import re

import click
from bs4 import BeautifulSoup
from flask import current_app
from flask.cli import with_appcontext

from backend.importer.http import SourceClient, SourceFetchError
from backend.importer.forms import FormNavigationError
from backend.importer.navigation import search_study, follow_named_result, submit_labeled_search


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


def register_cli(app):
    app.cli.add_command(source_check)
    app.cli.add_command(source_plan_check)
