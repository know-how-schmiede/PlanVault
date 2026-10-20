"""Flask-Anwendung für WI-PlanArchiv."""

from flask import Flask

from backend.config import load_config
from version import __version__


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(load_config())
    if test_config is not None:
        app.config.update(test_config)

    from backend.web import web

    app.register_blueprint(web)
    from backend.cli import register_cli

    register_cli(app)

    @app.context_processor
    def application_version():
        return {"app_version": __version__}

    return app
