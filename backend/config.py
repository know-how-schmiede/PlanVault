"""Konfiguration ohne eingebettete Quelladressen."""

import os


def load_config():
    return {
        "LSF_BASE_URL": os.environ.get("LSF_BASE_URL", ""),
        "TIMEZONE": "Europe/Berlin",
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }
