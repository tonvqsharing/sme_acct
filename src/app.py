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
from src.bricks.purchases.services import PurchaseService
from src.bricks.purchases.storage import (
    Base as PurchBase,
)
from src.bricks.purchases.storage import (
    SQLAlchemySupplierInvoiceRepository,
)
from src.bricks.purchases.web_adapter import init_purchases_service, purchases_bp
from src.bricks.system_settings.rate_windows import make_rate_gate
from src.bricks.system_settings.services import SystemSettingsService, VatDeclarationService
from src.bricks.system_settings.storage import (
    Base as SetBase,
)
from src.bricks.system_settings.storage import (
    SQLAlchemySystemSettingsRepository,
)
from src.bricks.system_settings.web_adapter import (
    init_settings_service,
    init_tax_rate_catalog_service,
    init_vat_declaration_service,
    settings_bp,
)
from src.bricks.voucher.services import AutoJournalService, VoucherService
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
    _key = os.environ.get("SECRET_KEY", "")
    app.config["SECRET_KEY"] = _key or "dev-secret-change-in-production"
    if not _key and not (app.config.get("TESTING") or (config or {}).get("TESTING")):
        raise RuntimeError("SECRET_KEY env var is required outside TESTING mode")
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
    PurchBase.metadata.create_all(engine)
    SetBase.metadata.create_all(engine)
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

    # ── Blueprints ──────────────────────────────────────────────────────
    for bp in (
        web_adapter_bp,
        payment_terms_bp,
        document_numbering_bp,
        invoice_bp,
        voucher_bp,
        ledger_bp,
        bank_cash_bp,
        purchases_bp,
        settings_bp,
        coa_bp,
        fiscal_year_bp,
        audit_log_bp,
    ):
        app.register_blueprint(bp)

    # ── Sessions ────────────────────────────────────────────────────────
    session = session_factory()
    bc_session = session_factory()
    pt_session = session_factory()
    pt_session2 = session_factory()
    inv_session = session_factory()
    voucher_session = session_factory()
    coa_session = session_factory()
    fy_session = session_factory()
    purchases_session = session_factory()

    # ── Company (tenant root) ───────────────────────────────────────────
    company_repo = SQLAlchemyCompanyRepository(session)
    company_svc = CompanyService(company_repo)
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

    # ── Audit ───────────────────────────────────────────────────────────
    audit_svc = AuditLogService(SQLAlchemyAuditLogRepository(session_factory()))
    init_audit_service(audit_svc)

    # ── COA + Fiscal Year (posting gates) ───────────────────────────────
    app.coa_service = AccountService(  # type: ignore[attr-defined]
        SQLAlchemyAccountRepository(coa_session)
    )
    app.fy_service = FiscalYearService(  # type: ignore[attr-defined]
        SQLAlchemyFiscalYearRepository(fy_session),
        SQLAlchemyPeriodRepository(fy_session),
    )
    init_coa_service(app.coa_service)
    init_fy_service(app.fy_service)

    class _CoaGate:
        def validate_posting_account(self, company_id, code, regime="tt133"):
            app.coa_service.validate_posting_account(company_id, code, regime)

    class _FyGate:
        def find_open_period(self, company_id, d):
            return app.fy_service.find_open_period(company_id, d)

    # ── Payment Terms + Numbering + SOD approvals ───────────────────────
    term_repo = SQLAlchemyPaymentTermRepository(pt_session)
    series_repo = SQLAlchemyDocumentNumberingSeriesRepository(pt_session)
    pt_term_svc = PaymentTermService(term_repo)

    from src.bricks.audit_log.storage import SQLAlchemyAuditLogRepository as _ALR

    pt_audit_svc = AuditLogService(_ALR(session_factory()))
    init_payment_terms_services(
        PaymentTermService(term_repo, audit=pt_audit_svc),
        DocumentNumberingSeriesService(series_repo, audit=pt_audit_svc),
    )

    dns_repo2 = SQLAlchemyDocumentNumberingSeriesRepository(pt_session2)
    dns_service = DocumentNumberingSeriesService(dns_repo2)

    approval_svc = ApprovalService(
        SQLAlchemyApprovalRequestRepository(session_factory()),
        term_service=PaymentTermService(term_repo),
        series_service=DocumentNumberingSeriesService(series_repo),
        audit=audit_svc,
    )
    from src.bricks.payment_terms.web_adapter import init_approval_service

    init_approval_service(approval_svc)

    # ── Tax-rate catalog (master data) + lawful fractions ───────────────
    from src.bricks.system_settings.domain import TaxRate as _TaxRate
    from src.bricks.system_settings.services import TaxRateCatalogService
    from src.bricks.system_settings.storage import (
        SQLAlchemyTaxRateWindowRepository,
    )

    catalog_svc = TaxRateCatalogService(SQLAlchemyTaxRateWindowRepository(session_factory()))
    init_tax_rate_catalog_service(catalog_svc)
    catalog_svc.ensure_seeded()
    RATE_GATE = make_rate_gate(tuple(catalog_svc.all_windows()))

    LAWFUL_VAT_FRACTIONS = frozenset(
        {r.to_fraction() for r in _TaxRate if r.value >= 0}
    )  # NOT_TAXED(-1) maps to 0; excluded from distinct membership

    # ── Bank / Cash (balance side-effects for vouchers) ─────────────────
    cash_svc_bc = CashAccountService(SQLAlchemyCashAccountRepository(bc_session))
    bank_svc_bc = BankAccountService(SQLAlchemyBankAccountRepository(bc_session))

    def _apply_cash_balances(voucher, actor, chief_approved: bool) -> None:
        """Mirror journal lines into cash balances BEFORE status flip."""
        cash_svc_bc.apply_journal(
            voucher.company_id,
            [
                {
                    "account_code": l.account_code,
                    "debit": str(l.debit),
                    "credit": str(l.credit),
                }
                for l in voucher.lines
            ],
            actor=actor,
            reason=f"voucher:{voucher.number}",
            chief_approved=chief_approved,
        )

    # ── Numbering adapters (HD* invoices, PT* vouchers) ─────────────────
    class _SeriesIssueAdapter:
        """Issues next number from company's first active series by prefix."""

        def __init__(self, dns, prefix_startswith: str):
            self._dns = dns
            self._prefix = prefix_startswith

        def issue(self, company_id):
            from uuid import NAMESPACE_URL, uuid5

            sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
            series = self._dns.list_by_company(company_id, active=True)
            target = next((x for x in series if x.prefix.startswith(self._prefix)), None)
            if target is None:
                raise RuntimeError(f"No active {self._prefix}* numbering series")
            seq = self._dns.increment_sequence(target.id, sys_actor, self._prefix.rstrip("/"))
            return f"{target.prefix}{seq:06d}"

    # ── Voucher brick ───────────────────────────────────────────────────
    class _TermsAdapter:
        def get_default(self, company_id):
            return pt_term_svc.get_default(company_id)

        def get_payment_term(self, tid):
            return pt_term_svc.get_payment_term(tid)

    voucher_svc = VoucherService(
        fy=_FyGate(),
        coa=_CoaGate(),
        numbering=_SeriesIssueAdapter(dns_service, "PT"),
        audit=audit_svc,
        repo=SQLAlchemyVoucherRepository(voucher_session),
        regime_of=regime_provider,
        on_posted=_apply_cash_balances,
    )
    init_voucher_service(voucher_svc)

    auto_journal = AutoJournalService(
        voucher_svc=voucher_svc,
        regime_provider=regime_provider,
    )

    # ── Invoice brick (consumes voucher auto-journal) ───────────────────
    invoice_svc = InvoiceService(
        fy=_FyGate(),
        coa=_CoaGate(),
        numbering=_SeriesIssueAdapter(dns_service, "HD"),
        terms=_TermsAdapter(),
        audit=audit_svc,
        repo=SQLAlchemyInvoiceRepository(inv_session),
        regime_of=regime_provider,
        allowed_vat_rates=LAWFUL_VAT_FRACTIONS,
        rate_gate=RATE_GATE,
    )
    init_invoice_service(invoice_svc, on_posted=auto_journal.build_for)

    # ── Purchases brick ─────────────────────────────────────────────────
    purchases_repo = SQLAlchemySupplierInvoiceRepository(purchases_session)
    init_purchases_service(
        PurchaseService(
            repo=purchases_repo,
            fy=_FyGate(),
            coa=_CoaGate(),
            regime_of=regime_provider,
            allowed_vat_rates=LAWFUL_VAT_FRACTIONS,
            rate_gate=RATE_GATE,
        )
    )

    # ── Ledger reports + VAT declaration (read-only) ────────────────────
    ledger_source = SQLAlchemyLedgerSource(session_factory())
    ledger_svc = LedgerService(source=ledger_source)
    init_ledger_service(ledger_svc)

    def _decl_input_source(company_id, start, end):
        """POSTED purchase invoices in window -> primitive dicts (SQL-filtered)."""
        return [
            {
                "invoice_number": inv.invoice_number,
                "status": inv.status.value,
                "deductibility": inv.deductibility.value,
                "vat_deductible": str(inv.vat_deductible),
            }
            for inv in purchases_repo.get_posted_between(company_id, start, end)
        ]

    init_vat_declaration_service(
        VatDeclarationService(
            output_source=ledger_source.get_posted_lines,
            input_source=_decl_input_source,
        )
    )

    # ── System settings + bank reconciliation ───────────────────────────
    init_settings_service(
        SystemSettingsService(SQLAlchemySystemSettingsRepository(session_factory()))
    )

    from decimal import Decimal

    from src.bricks.bank_cash.services import ReconciliationService
    from src.bricks.bank_cash.storage import (
        SQLAlchemyReconciliationRepository,
    )

    class _BankInternalBalanceProvider:
        """Σ(debit-credit) over POSTED voucher lines tagged to a bank."""

        def __init__(self, session):
            self._session = session

        def __call__(self, company_id, bank_account_id, as_of):
            from src.bricks.voucher.storage import VoucherModel

            rows = (
                self._session.query(VoucherModel)
                .filter(
                    VoucherModel.company_id == str(company_id),
                    VoucherModel.status == "POSTED",
                )
                .all()
            )
            total = Decimal(0)
            target = str(bank_account_id)
            for v in rows:
                if v.entry_date > as_of:
                    continue
                for ln in v.lines:
                    if ln.get("bank_account_id") != target:
                        continue
                    total += Decimal(ln["debit"]) - Decimal(ln["credit"])
            return total

    init_bank_cash_services(
        bank_svc_bc,
        cash_svc_bc,
        ReconciliationService(
            SQLAlchemyReconciliationRepository(bc_session),
            internal_provider=_BankInternalBalanceProvider(session_factory()),
        ),
    )

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
