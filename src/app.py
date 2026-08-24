"""Flask application factory.

Creates and configures the Flask app, initializes extensions,
and registers brick blueprints.
"""

from __future__ import annotations

import os

from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.bricks.audit_log.services import AuditLogService
from src.bricks.audit_log.storage import (
    Base as AuditBase,
)
from src.bricks.audit_log.storage import (
    SQLAlchemyAuditLogRepository,
)
from src.bricks.company.services import CompanyService, TenantService
from src.bricks.company.storage import Base as CompanyBase
from src.bricks.company.storage import SQLAlchemyCompanyRepository
from src.bricks.company.web_adapter import init_company_services, web_adapter_bp
from src.bricks.payment_terms.services import (
    DocumentNumberingSeriesService,
    PaymentTermService,
)
from src.bricks.payment_terms.storage import (
    Base as PaymentTermsBase,
)
from src.bricks.payment_terms.storage import (
    SQLAlchemyDocumentNumberingSeriesRepository,
    SQLAlchemyPaymentTermRepository,
)
from src.bricks.payment_terms.web_adapter import (
    document_numbering_bp,
    init_payment_terms_services,
    payment_terms_bp,
)


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional config dict override.

    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)

    # Default config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
    )
    if config:
        app.config.update(config)

    # ── Database ────────────────────────────────────────────────────────
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    CompanyBase.metadata.create_all(engine)
    PaymentTermsBase.metadata.create_all(engine)
    AuditBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    app.db_session = session_factory  # type: ignore[attr-defined]

    # ── Flask-Login ─────────────────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        # Placeholder — will be replaced when user brick is implemented
        return None

    # ── Wire Company brick services ─────────────────────────────────────
    session = session_factory()
    repo = SQLAlchemyCompanyRepository(session)
    company_svc = CompanyService(repo)
    tenant_svc = TenantService(company_svc)
    init_company_services(company_svc, tenant_svc)

    # ── Wire Payment Terms brick services ───────────────────────────────
    pt_session = session_factory()
    term_repo = SQLAlchemyPaymentTermRepository(pt_session)
    series_repo = SQLAlchemyDocumentNumberingSeriesRepository(pt_session)
    init_payment_terms_services(
        PaymentTermService(term_repo),
        DocumentNumberingSeriesService(series_repo),
    )
    from src.bricks.payment_terms.storage import (
        SQLAlchemyApprovalRequestRepository,
    )

    audit_svc = AuditLogService(SQLAlchemyAuditLogRepository(session_factory()))
    from src.bricks.payment_terms.services import ApprovalService

    approval_svc = ApprovalService(
        SQLAlchemyApprovalRequestRepository(session_factory()),
        term_service=PaymentTermService(term_repo),
        series_service=DocumentNumberingSeriesService(series_repo),
        audit=audit_svc,
    )

    # ── Register blueprints ─────────────────────────────────────────────
    app.register_blueprint(web_adapter_bp)
    app.register_blueprint(payment_terms_bp)
    app.register_blueprint(document_numbering_bp)

    from src.bricks.payment_terms.web_adapter import init_approval_service

    init_approval_service(approval_svc)

    # ── Health check ────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return {"status": "ok"}

    # ── Placeholder login (will be replaced by auth brick) ─────────────
    @app.route("/login", methods=["GET", "POST"])
    def login():
        return {"message": "Login not implemented yet"}, 501

    return app


# ── Dev server entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5000)
