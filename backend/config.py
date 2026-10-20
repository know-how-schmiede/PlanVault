"""Konfiguration ohne eingebettete Quelladressen."""

import os


def load_config():
    return {
        "LSF_BASE_URL": os.environ.get("LSF_BASE_URL", ""),
        "LSF_ID_PARAMETER": os.environ.get("LSF_ID_PARAMETER", ""),
        "LSF_ID_NAMESPACE": os.environ.get("LSF_ID_NAMESPACE", ""),
        "TIMEZONE": "Europe/Berlin",
        "PREVIEW_FILE": os.environ.get("PREVIEW_FILE", ""),
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }
