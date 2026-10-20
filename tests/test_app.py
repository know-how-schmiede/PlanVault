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


def test_brand_is_local_and_accessible():
    from bs4 import BeautifulSoup
    app = create_app({"TESTING": True})
    client = app.test_client()
    soup = BeautifulSoup(client.get("/").data, "html.parser")
    logo = soup.select_one("header .brand img")
    assert logo is not None and "WI-PlanArchiv" in logo["alt"]
    assert logo.find_parent("a")["href"] == "/"
    response = client.get(logo["src"])
    assert response.status_code == 200 and response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    from pathlib import Path
    asset = Path(__file__).resolve().parents[1] / "images" / "WI-PlanArchiv_ Vorlesungsplanung gesichert.png"
    assert response.data == asset.read_bytes()
    assert soup.select_one("header .hero-copy h1").get_text() == "Dein Vorlesungsplan verdient ein Archiv."
    assert len(soup.find_all("h1")) == 1
    assert "Vorlesungsplanung sichern" not in soup.get_text()
    assert len(soup.select(".next-steps li")) == 3