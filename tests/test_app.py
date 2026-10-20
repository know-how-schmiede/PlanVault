from backend import create_app
from version import __version__


def test_start_without_source_displays_honest_status_and_version(monkeypatch):
    monkeypatch.delenv("LSF_BASE_URL", raising=False)
    app = create_app({"TESTING": True})
    assert app.config["LSF_BASE_URL"] == ""
    response = app.test_client().get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"Version V{__version__}" in html
    assert "Letzte erfolgreiche Sicherung: noch keine." in html


def test_source_configuration_is_never_rendered(monkeypatch):
    marker = "VERTRAULICHER_TESTWERT"
    monkeypatch.setenv("LSF_BASE_URL", marker)
    app = create_app({"TESTING": True})
    assert app.config["LSF_BASE_URL"] == marker
    assert marker not in app.test_client().get("/").get_data(as_text=True)


def test_stylesheet_is_available():
    app = create_app({"TESTING": True})
    response = app.test_client().get("/static/style.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"
