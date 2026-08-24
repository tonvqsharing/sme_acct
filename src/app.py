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
from src.bricks.audit_log.web_adapter import (
    audit_log_bp,
    init_audit_service,
)
from src.bricks.bank_cash.services import BankAccountService, CashAccountService
from src.bricks.bank_cash.storage import (
    Base as BankBase,
)
from src.bricks.bank_cash.storage import (
    SQLAlchemyBankAccountRepository,
    SQLAlchemyCashAccountRepository,
)
from src.bricks.bank_cash.web_adapter import bank_cash_bp, init_bank_cash_services
from src.bricks.coa.services import AccountService
from src.bricks.coa.storage import Base as CoaBase
from src.bricks.coa.storage import SQLAlchemyAccountRepository
from src.bricks.coa.web_adapter import coa_bp, init_coa_service
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
from src.bricks.fiscal_year_period.web_adapter import (
    fiscal_year_bp,
    init_fy_service,
)
from src.bricks.invoice.services import InvoiceService
from src.bricks.invoice.storage import Base as InvBase
from src.bricks.invoice.storage import SQLAlchemyInvoiceRepository
from src.bricks.invoice.web_adapter import init_invoice_service, invoice_bp
from src.bricks.ledger.services import LedgerService
from src.bricks.ledger.storage import SQLAlchemyLedgerSource
from src.bricks.ledger.web_adapter import init_ledger_service, ledger_bp
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
    BankBase.metadata.create_all(engine)
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

    class _RegimeOf:
        """company_id -> regime string via company contract."""

        def __init__(self, company_svc):
            self._companies = company_svc

        def __call__(self, company_id):
            c = self._companies.get_by_id(company_id)
            return c.accounting_regime.value if c else "tt133"

    regime_provider = _RegimeOf(company_svc)

    # ── Wire Payment Terms brick services ───────────────────────────────
    pt_session = session_factory()
    term_repo = SQLAlchemyPaymentTermRepository(pt_session)
    series_repo = SQLAlchemyDocumentNumberingSeriesRepository(pt_session)
    pt_audit = session_factory()  # dedicated session for audit writes
    from src.bricks.audit_log.storage import SQLAlchemyAuditLogRepository as _ALR

    _pt_audit_svc = AuditLogService(_ALR(pt_audit))
    init_payment_terms_services(
        PaymentTermService(term_repo, audit=_pt_audit_svc),
        DocumentNumberingSeriesService(series_repo, audit=_pt_audit_svc),
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
    app.register_blueprint(ledger_bp)
    app.register_blueprint(bank_cash_bp)
    app.register_blueprint(coa_bp)
    app.register_blueprint(fiscal_year_bp)
    app.register_blueprint(audit_log_bp)

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
        regime_of=_RegimeOf(company_svc),
    )

    def _auto_journal(posted_invoice):
        """Posting an invoice generates + posts its balanced journal."""
        from uuid import NAMESPACE_URL, uuid5

        from src.bricks.coa.domain import resolve_chart_role

        sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
        regime = regime_provider(posted_invoice.company_id)
        role_codes = {
            role: resolve_chart_role(role, regime) for role in ("ar", "revenue", "vat_output")
        }
        v = voucher_svc.create_voucher(
            company_id=posted_invoice.company_id,
            entry_date=posted_invoice.issue_date,
            description=f"Auto journal for {posted_invoice.number}",
            lines=[
                {"account_code": l.account_code, "debit": str(l.debit), "credit": str(l.credit)}
                for l in InvoiceServiceAdapter.lines_from_invoice(posted_invoice, role_codes)
            ],
            actor=sys_actor,
            reason=f"auto:{posted_invoice.number}",
        )
        posted = voucher_svc.post_voucher(
            v.id,
            actor=sys_actor,
            reason=f"auto:{posted_invoice.number}",
        )
        return {"id": str(posted.id), "number": posted.number}

    init_invoice_service(invoice_svc, on_posted=_auto_journal)

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

    cash_repo_bc = SQLAlchemyCashAccountRepository(session_factory())
    cash_svc_bc = CashAccountService(cash_repo_bc)

    def _apply_cash_balances(voucher, actor, chief_approved: bool) -> None:
        """Mirror journal lines into cash-account balances (pre-check)."""
        cash_svc_bc.apply_journal(
            voucher.company_id,
            [
                {"account_code": l.account_code, "debit": str(l.debit), "credit": str(l.credit)}
                for l in voucher.lines
            ],
            actor=actor,
            reason=f"voucher:{voucher.number}",
            chief_approved=chief_approved,
        )

    voucher_svc = VoucherService(
        fy=app.fy_service,
        coa=app.coa_service,
        numbering=_VNumbering(dns_service),
        audit=audit_svc,
        repo=SQLAlchemyVoucherRepository(session_factory()),
        regime_of=_RegimeOf(company_svc),
        on_posted=_apply_cash_balances,
    )
    init_voucher_service(voucher_svc)

    from src.bricks.voucher.services import InvoiceServiceAdapter

    ledger_svc = LedgerService(source=SQLAlchemyLedgerSource(session_factory()))
    init_ledger_service(ledger_svc)
    init_coa_service(app.coa_service)

    bc_session = session_factory()
    init_bank_cash_services(
        BankAccountService(SQLAlchemyBankAccountRepository(bc_session)),
        CashAccountService(SQLAlchemyCashAccountRepository(bc_session)),
    )
    init_fy_service(app.fy_service)
    init_audit_service(audit_svc)

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
