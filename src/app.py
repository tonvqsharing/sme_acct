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
from src.bricks.coa.services import AccountService
from src.bricks.coa.storage import Base as CoaBase
from src.bricks.coa.storage import SQLAlchemyAccountRepository
from src.bricks.company.services import CompanyService, TenantService
from src.bricks.company.storage import Base as CompanyBase
from src.bricks.company.storage import SQLAlchemyCompanyRepository
from src.bricks.company.web_adapter import init_company_services, web_adapter_bp
from src.bricks.fiscal_year_period.services import FiscalYearService
from src.bricks.fiscal_year_period.storage import (
    Base as FyBase,
)
from src.bricks.fiscal_year_period.storage import (
    SQLAlchemyFiscalYearRepository,
    SQLAlchemyPeriodRepository,
)
from src.bricks.invoice.services import InvoiceService
from src.bricks.invoice.storage import Base as InvBase
from src.bricks.invoice.storage import SQLAlchemyInvoiceRepository
from src.bricks.invoice.web_adapter import init_invoice_service, invoice_bp
from src.bricks.payment_terms.services import (
    ApprovalService,
    DocumentNumberingSeriesService,
    PaymentTermService,
)
from src.bricks.payment_terms.storage import (
    Base as PaymentTermsBase,
)
from src.bricks.payment_terms.storage import (
    SQLAlchemyApprovalRequestRepository,
    SQLAlchemyDocumentNumberingSeriesRepository,
    SQLAlchemyPaymentTermRepository,
)
from src.bricks.payment_terms.web_adapter import (
    document_numbering_bp,
    init_payment_terms_services,
    payment_terms_bp,
)
from src.bricks.voucher.services import VoucherService
from src.bricks.voucher.storage import Base as VchBase
from src.bricks.voucher.storage import SQLAlchemyVoucherRepository
from src.bricks.voucher.web_adapter import init_voucher_service, voucher_bp


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
    CoaBase.metadata.create_all(engine)
    FyBase.metadata.create_all(engine)
    InvBase.metadata.create_all(engine)
    VchBase.metadata.create_all(engine)
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

    audit_svc = AuditLogService(SQLAlchemyAuditLogRepository(session_factory()))
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
    app.register_blueprint(invoice_bp)
    app.register_blueprint(voucher_bp)

    from src.bricks.payment_terms.web_adapter import init_approval_service

    init_approval_service(approval_svc)

    # ── Wire COA + Fiscal Year bricks ────────────────────────────────────
    coa_session = session_factory()
    fy_session = session_factory()
    app.coa_service = AccountService(SQLAlchemyAccountRepository(coa_session))  # type: ignore[attr-defined]
    app.fy_service = FiscalYearService(  # type: ignore[attr-defined]
        SQLAlchemyFiscalYearRepository(fy_session),
        SQLAlchemyPeriodRepository(fy_session),
    )

    # ── Wire Invoice brick ───────────────────────────────────────────────
    class _NumberingAdapter:
        """Issues next number from company's first active HD* series."""

        def __init__(self, dns):
            self._dns = dns

        def issue(self, company_id):
            series = self._dns.list_by_company(company_id, active=True)
            target = next((x for x in series if x.prefix.startswith("HD")), None)
            if target is None:
                raise RuntimeError("No active HD/ numbering series")
            from uuid import NAMESPACE_URL, uuid5

            sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
            seq = self._dns.increment_sequence(target.id, sys_actor, "invoice")
            return f"{target.prefix}{seq:06d}"

    class _TermsAdapter:
        def __init__(self, svc):
            self._svc = svc

        def get_default(self, company_id):
            return self._svc.get_default(company_id)

        def get_payment_term(self, tid):
            return self._svc.get_payment_term(tid)

    inv_session = session_factory()
    pt_session2 = session_factory()
    dns_repo = SQLAlchemyDocumentNumberingSeriesRepository(pt_session2)
    dns_service = DocumentNumberingSeriesService(dns_repo)
    pt_repo2 = SQLAlchemyPaymentTermRepository(pt_session2)
    invoice_svc = InvoiceService(
        fy=app.fy_service,
        coa=app.coa_service,
        numbering=_NumberingAdapter(dns_service),
        terms=_TermsAdapter(PaymentTermService(pt_repo2)),
        audit=audit_svc,
        repo=SQLAlchemyInvoiceRepository(inv_session),
    )
    init_invoice_service(invoice_svc)

    class _VNumbering:
        def __init__(self, dns):
            self._dns = dns

        def issue(self, company_id):
            from uuid import NAMESPACE_URL, uuid5

            sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
            series = self._dns.list_by_company(company_id, active=True)
            target = next((x for x in series if x.prefix.startswith("PT")), None)
            if target is None:
                raise RuntimeError("No active PT/ numbering series")
            seq = self._dns.increment_sequence(target.id, sys_actor, "voucher")
            return f"{target.prefix}{seq:06d}"

    voucher_svc = VoucherService(
        fy=app.fy_service,
        coa=app.coa_service,
        numbering=_VNumbering(dns_service),
        audit=audit_svc,
        repo=SQLAlchemyVoucherRepository(session_factory()),
    )
    init_voucher_service(voucher_svc)

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
