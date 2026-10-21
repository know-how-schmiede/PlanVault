"""Tests verwenden ausschließlich explizit gesetzte fiktive Laufzeitwerte."""

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_runtime_environment(monkeypatch):
    # runuser kann exportierte Betreiberwerte vom Update-Aufruf übernehmen.
    # Vor jeder Test-Fixture entfernen; Tests setzen eigene Werte mit monkeypatch.
    for name in tuple(os.environ):
        if name.startswith('LSF_') or name == 'PREVIEW_FILE':
            monkeypatch.delenv(name)
