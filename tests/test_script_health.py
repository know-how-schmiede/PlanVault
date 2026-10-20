"""Die tatsächlich in den Setup-Skripten eingebettete HTTP-Prüfung ausführen."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]


def script_body(name):
    text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
    return text.split("<<'PY_HEALTH'\n", 1)[1].split("\nPY_HEALTH", 1)[0]


def test_both_scripts_use_the_same_health_check():
    assert script_body("install-debian13.sh") == script_body("update-debian13.sh")


@pytest.mark.parametrize("status,body,version,delay,success", [
    (200, b"OK", "", 0, True),
    (200, b"Version V0.0.18", "0.0.18", 0, True),
    (200, b"Version V0.0.18", "0.0.1", 0, False),
    (200, b"Version V0.0.17", "0.0.18", 0, False),
    (404, b"Version V0.0.18", "0.0.18", 0, False),
    (302, b"", "", 0, False),
    (200, b"x" * 1_000_001, "", 0, False),
    (200, b"OK", "", .3, False),
], ids=["ok", "version", "version-prefix", "wrong-version", "not-found", "redirect", "too-large", "timeout"])
def test_health_status_version_size_and_timeout(status, body, version, delay, success):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(delay)
            try:
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body)
            except OSError:
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
    thread.start()
    try:
        result = subprocess.run([sys.executable, "-c", script_body("update-debian13.sh"),
                                 str(server.server_port), ".05" if delay else "2", version],
                                capture_output=True, timeout=5,
                                env={**os.environ, "http_proxy": "http://invalid.invalid:9"})
        assert (result.returncode == 0) is success
        assert result.stdout == result.stderr == b""
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
