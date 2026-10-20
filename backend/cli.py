"""Manuelle Diagnose; kein Quellzugriff durch normale Webseitenaufrufe."""

import re

import click
from bs4 import BeautifulSoup
from flask import current_app
from flask.cli import with_appcontext

from backend.importer.http import SourceClient, SourceFetchError


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


def register_cli(app):
    app.cli.add_command(source_check)
