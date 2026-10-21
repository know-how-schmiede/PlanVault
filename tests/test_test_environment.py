"""Regression für Update-Tests aus einer bereits konfigurierten Importshell."""

import os
from pathlib import Path
import subprocess
import sys

from backend import create_app


def test_default_app_has_no_operator_source_or_preview_configuration():
    app = create_app({'TESTING': True})
    for name in ('LSF_BASE_URL', 'LSF_ID_PARAMETER', 'LSF_ID_NAMESPACE', 'PREVIEW_FILE'):
        assert app.config[name] == ''


def test_affected_cli_tests_pass_with_inherited_operator_configuration():
    environment = dict(os.environ)
    environment.update({
        'LSF_BASE_URL': 'https://example.invalid/operator',
        'LSF_ID_PARAMETER': 'runtime_record',
        'LSF_ID_NAMESPACE': 'FIKTIVER-LAUFZEITWERT',
        'LSF_STUDY_QUERY': 'Fiktive Betreiberwahl',
        'LSF_STUDY_TITLE': 'Fiktiver Betreiberstudiengang',
        'LSF_SEMESTER': 'FIKTIVES-SEMESTER',
        'LSF_STUDY_KEY': 'FIKTIV-STUDIUM',
        'LSF_REGULATIONS_KEY': 'FIKTIV-PO',
        'PREVIEW_FILE': '/tmp/fiktiver-betreiberstand.preview.json',
        'PYTHONDONTWRITEBYTECODE': '1',
    })
    result = subprocess.run([
        sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_details.py::test_cli_sample_summary_has_no_source_data',
        'tests/test_import_run.py::test_cli_json_remains_parseable_with_nonzero_exit',
    ], cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
