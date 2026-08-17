import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
talisman = Talisman()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["DEBUG"] = os.getenv("DEBUG", "1") == "1"

    # Multi-DB support: sqlite, mariadb, mysql, postgresql v16+
    # URIs: sqlite:///..., mysql://..., mariadb://..., postgresql://...
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///sme_acct.db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Talisman: enforce HTTPS only when not in DEBUG
    if not app.config["DEBUG"]:
        talisman.init_app(
            app,
            force_https=True,
            strict_transport_security=True,
            content_security_policy={
                "default-src": "'self'",
                "script-src": ["'self'", "cdn.jsdelivr.net"],
                "style-src": ["'self'", "cdn.jsdelivr.net", "'unsafe-inline'"],
            },
        )

    # Blueprints
    from src.presentation.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("base.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config["DEBUG"])
