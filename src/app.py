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
from src.bricks.cost_centers.services import (
    CostCenterService,
    DimensionService,
    DimensionValueService,
)
from src.bricks.cost_centers.storage import (
    Base as CcBase,
)
from src.bricks.cost_centers.storage import (
    SQLAlchemyCostCenterRepository,
    SQLAlchemyDimensionRepository,
    SQLAlchemyDimensionValueRepository,
)
from src.bricks.cost_centers.web_adapter import (
    cost_centers_bp,
    init_cost_center_service,
    init_dimension_service,
    init_dimension_value_service,
)
from src.bricks.currencies.services import (
    CurrencyService,
    ExchangeRateService,
    RevaluationService,
)
from src.bricks.currencies.storage import (
    Base as CurBase,
)
from src.bricks.currencies.storage import (
    SQLAlchemyCurrencyRepository,
)
from src.bricks.currencies.web_adapter import (
    init_currencies_services,
)
from src.bricks.document_conversion.services import DocumentConversionService
from src.bricks.document_conversion.storage import Base as DocConvBase
from src.bricks.document_conversion.web_adapter import bp as document_conversion_bp
from src.bricks.document_conversion.web_adapter import init_document_conversion

# Financial Statements brick
from src.bricks.financial_statements.storage import (
    Base as FsBase,
)
from src.bricks.financial_statements.storage import (
    SQLAlchemyReportInstanceRepository,
    SQLAlchemyReportTemplateRepository,
    SQLAlchemyRetainedEarningsRepository,
)
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
from src.bricks.fixed_assets.services import FixedAssetService
from src.bricks.fixed_assets.storage import (
    Base as Fabase,
)
from src.bricks.fixed_assets.storage import (
    SQLAlchemyFixedAssetRepository,
)
from src.bricks.fixed_assets.web_adapter import (
    fixed_assets_bp,
    init_fixed_assets_service,
)
from src.bricks.inventory.services import InventoryService
from src.bricks.inventory.storage import Base as InvtyBase
from src.bricks.inventory.storage import SQLAlchemyInventoryRepository
from src.bricks.inventory.web_adapter import init_inventory_service, inventory_bp
from src.bricks.invoice.services import InvoiceService
from src.bricks.invoice.storage import Base as InvBase
from src.bricks.invoice.storage import SQLAlchemyInvoiceRepository
from src.bricks.invoice.web_adapter import init_invoice_service, invoice_bp
from src.bricks.ledger.services import LedgerService
from src.bricks.ledger.storage import SQLAlchemyLedgerSource
from src.bricks.ledger.web_adapter import init_ledger_service, ledger_bp
from src.bricks.party.services import PartyService
from src.bricks.party.storage import Base as PartyBase
from src.bricks.party.storage import SQLAlchemyPartyRepository
from src.bricks.party.web_adapter import init_party_service, party_bp
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

# Tools & Equipment (CCDC) brick
from src.bricks.tools_equipment.services import AllocationEngine, ToolEquipmentService
from src.bricks.tools_equipment.storage import (
    Base as TeBase,
)
from src.bricks.tools_equipment.storage import (
    ToolEquipmentAllocationRepo,
    ToolEquipmentRepo,
)
from src.bricks.tools_equipment.web_adapter import (
    bp as tools_equipment_bp,
)
from src.bricks.tools_equipment.web_adapter import (
    init_tools_equipment_bp,
)
from src.bricks.uom.services import UOMService
from src.bricks.uom.storage import Base as UOMBase
from src.bricks.uom.storage import SQLAlchemyUOMRepository
from src.bricks.uom.web_adapter import init_uom_service, uom_bp
from src.bricks.user_master_data.services import UserService
from src.bricks.user_master_data.storage import (
    Base as UserBase,
)
from src.bricks.user_master_data.storage import (
    SQLAlchemyUserRepository,
)
from src.bricks.user_master_data.web_adapter import (
    auth_bp,
    init_user_service,
    users_bp,
)
from src.bricks.voucher.services import AutoJournalService, VoucherService
from src.bricks.voucher.storage import Base as VchBase
from src.bricks.voucher.storage import SQLAlchemyVoucherRepository
from src.bricks.voucher.web_adapter import init_voucher_service, voucher_bp
from src.bricks.xml_ingest.services import XMLIngestService
from src.bricks.xml_ingest.web_adapter import init_xml_ingest_service, xml_ingest_bp


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
    CurBase.metadata.create_all(engine)
    Fabase.metadata.create_all(engine)
    CcBase.metadata.create_all(engine)
    VchBase.metadata.create_all(engine)
    UserBase.metadata.create_all(engine)
    TeBase.metadata.reflect(bind=engine)
    TeBase.metadata.create_all(engine)
    FsBase.metadata.create_all(engine)
    DocConvBase.metadata.create_all(engine)
    InvtyBase.metadata.create_all(engine)
    PartyBase.metadata.create_all(engine)
    UOMBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    app.db_session = session_factory  # type: ignore[attr-defined]

    # ── Flask-Login ─────────────────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    user_repo_auth = SQLAlchemyUserRepository(session_factory())
    user_svc_auth = UserService(user_repo_auth)

    @login_manager.user_loader
    def load_user(user_id: str):
        from uuid import UUID as _U

        try:
            return user_repo_auth.get_by_id(_U(user_id))
        except (ValueError, TypeError):
            return None

    from flask import jsonify as _jsonify

    @login_manager.unauthorized_handler
    def _unauthorized():
        return _jsonify({"error": "Yêu cầu đăng nhập", "code": "UNAUTHENTICATED"}), 401

    # ── Blueprints ──────────────────────────────────────────────────────
    for bp in (
        auth_bp,
        users_bp,
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
        tools_equipment_bp,
        xml_ingest_bp,
        document_conversion_bp,
        inventory_bp,
        party_bp,
        uom_bp,
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
    invty_session = session_factory()
    party_session = session_factory()
    uom_session = session_factory()

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
    init_user_service(user_svc_auth)

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
    from src.bricks.system_settings.services import TaxRateCatalogService
    from src.bricks.system_settings.storage import (
        SQLAlchemyTaxRateWindowRepository,
    )

    catalog_svc = TaxRateCatalogService(SQLAlchemyTaxRateWindowRepository(session_factory()))
    init_tax_rate_catalog_service(catalog_svc)
    catalog_svc.ensure_seeded()
    RATE_GATE = make_rate_gate(tuple(catalog_svc.all_windows()))

    from src.bricks.system_settings.contract import (
        ALLOWED_VAT_FRACTIONS as LAWFUL_VAT_FRACTIONS,  # str set, mypy clean
    )

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

    # ── Invoice brick (consumes voucher auto-journal + deduction) ───────
    from src.bricks.system_settings.storage import SQLAlchemyPeriodLockRepository as _PLR2

    _inv_period_lock = _PLR2(session_factory())
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
        period_lock=_inv_period_lock,
    )
    init_invoice_service(invoice_svc, on_posted=auto_journal.build_for, voucher_service=voucher_svc)

    # ── Inventory brick (Tryton stock parity, TT99 4 methods, no 611) ───
    class _InventoryNumbering:  # type: ignore[no-redef]
        def __init__(self, dns):
            self._dns = dns

        def issue(self, company_id, ship_type):  # ship_type is ShipmentType
            from uuid import NAMESPACE_URL, uuid5

            sys_actor = uuid5(NAMESPACE_URL, "system:numbering")
            prefix_map = {"supplier_in": "PN/", "customer_out": "PX/", "internal": "CK/"}
            pfx = prefix_map.get(
                ship_type.value if hasattr(ship_type, "value") else str(ship_type), "CK/"
            )
            series = self._dns.list_by_company(company_id, active=True)
            target = next((x for x in series if x.prefix.startswith(pfx)), None)
            if target is None:
                raise RuntimeError(f"No active {pfx}* inventory series")
            seq = self._dns.increment_sequence(target.id, sys_actor, pfx.rstrip("/"))
            return f"{pfx}{seq:06d}"

    invty_repo = SQLAlchemyInventoryRepository(invty_session)
    inventory_svc = InventoryService(
        repo=invty_repo,
        fy=_FyGate(),
        numbering=_InventoryNumbering(dns_service),
        audit=audit_svc,
        voucher_service=voucher_svc,
        coa=app.coa_service,
        regime_of=regime_provider,
    )
    init_inventory_service(inventory_svc)
    app.inventory_service = inventory_svc  # type: ignore[attr-defined]

    # ── Party brick (Tryton party base: Customer/Supplier/Employee) ─────
    party_repo = SQLAlchemyPartyRepository(party_session)
    party_svc = PartyService(repo=party_repo, audit=audit_svc)
    init_party_service(party_svc)
    app.party_service = party_svc  # type: ignore[attr-defined]

    # ── UOM brick ───────────────────────────────────────────────────────
    uom_repo = SQLAlchemyUOMRepository(uom_session)
    uom_svc = UOMService(repo=uom_repo, audit=audit_svc)
    init_uom_service(uom_svc)
    app.uom_service = uom_svc  # type: ignore[attr-defined]

    # ── Purchases brick ─────────────────────────────────────────────────
    purchases_repo = SQLAlchemySupplierInvoiceRepository(purchases_session)
    purchase_svc = PurchaseService(
        repo=purchases_repo,
        fy=_FyGate(),
        coa=_CoaGate(),
        regime_of=regime_provider,
        allowed_vat_rates=LAWFUL_VAT_FRACTIONS,
        rate_gate=RATE_GATE,
    )
    init_purchases_service(purchase_svc)

    # ── Document Conversion brick (MarkItDown) ─────────────────────────
    doc_conv_svc = DocumentConversionService()
    init_document_conversion(doc_conv_svc)

    # ── XML Ingest brick ─────────────────────────────────────────────────
    xml_ingest_svc = XMLIngestService(purchase_service=purchase_svc)
    init_xml_ingest_service(xml_ingest_svc)

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

    fa_session = session_factory()
    init_fixed_assets_service(
        FixedAssetService(
            repo=SQLAlchemyFixedAssetRepository(fa_session),
            coa_gate=app.coa_service,
        )
    )

    from src.bricks.system_settings.storage import (
        SQLAlchemyVatCarryRepository,
    )

    _vat_carry_repo = SQLAlchemyVatCarryRepository(session_factory())
    _settings_for_vat = SQLAlchemySystemSettingsRepository(session_factory())
    init_vat_declaration_service(
        VatDeclarationService(
            output_source=ledger_source.get_posted_lines,
            input_source=_decl_input_source,
            carry_repo=_vat_carry_repo,
            config_repo=_settings_for_vat,
        )
    )

    # ── TaxCode master detail ───────────────────────────────────────────
    from src.bricks.system_settings.services import TaxCodeService
    from src.bricks.system_settings.storage import SQLAlchemyTaxCodeRepository
    from src.bricks.system_settings.web_adapter import init_tax_code_service

    tax_code_repo = SQLAlchemyTaxCodeRepository(session_factory())
    tax_code_svc = TaxCodeService(repo=tax_code_repo, audit=audit_svc)
    init_tax_code_service(tax_code_svc)
    app.tax_code_service = tax_code_svc  # type: ignore[attr-defined]

    # ── System settings + bank reconciliation ───────────────────────────
    class _FxItemsProvider:
        """v1: FX balances come from bank accounts tagged per currency."""

        def __call__(self, company_id):
            return []

    from src.bricks.currencies.storage import (
        SQLAlchemyExchangeRateRepository,
        SQLAlchemyRevaluationRunRepository,
    )

    cur_session = session_factory()
    cur_repo_cur = SQLAlchemyCurrencyRepository(cur_session)
    cur_svc = CurrencyService(cur_repo_cur)
    cur_svc.ensure_base_currency()
    rate_repo_cur = SQLAlchemyExchangeRateRepository(cur_session)
    rate_svc_cur = ExchangeRateService(rate_repo_cur)
    reval_svc_cur = RevaluationService(
        rates=rate_svc_cur,
        repo=SQLAlchemyRevaluationRunRepository(cur_session),
        monetary_items=_FxItemsProvider(),
        period_locked=lambda cid: False,
    )
    init_currencies_services(cur_svc, rate_svc_cur, reval_svc_cur)

    from src.bricks.currencies.web_adapter import currencies_bp as _cbp_inner

    if "currencies_bp" not in dir():
        pass
    app.register_blueprint(_cbp_inner)
    app.register_blueprint(fixed_assets_bp)
    app.register_blueprint(cost_centers_bp)

    # -- Cost Centers + Dimensions services --------------------------------
    cc_repo = SQLAlchemyCostCenterRepository(session_factory())
    cc_svc = CostCenterService(cc_repo)
    init_cost_center_service(cc_svc)

    dim_repo = SQLAlchemyDimensionRepository(session_factory())
    dim_svc = DimensionService(dim_repo)
    init_dimension_service(dim_svc)

    dv_repo = SQLAlchemyDimensionValueRepository(session_factory())
    dv_svc = DimensionValueService(dv_repo, dim_repo)
    init_dimension_value_service(dv_svc)

    # ── Tools & Equipment (CCDC) ─────────────────────────────────────────
    class _COAServiceAdapter:
        """Adapt AccountService to COAServicePort for CCDC brick."""

        def __init__(self, coa_svc):
            self._coa = coa_svc

        def is_account_active(self, company_id, account_code: str) -> bool:
            try:
                acct = self._coa.get_account(company_id, account_code)
                if acct is None:
                    return False
                return acct.status.value == "active"
            except (AttributeError, ValueError, TypeError):
                return False

        def is_account_detail(self, company_id, account_code: str) -> bool:
            acct = self._coa.get_account(company_id, account_code)
            if acct is None:
                return False
            return getattr(acct, "is_detail", False)

        def get_account(self, company_id, account_code: str) -> dict | None:
            acct = self._coa.get_account(company_id, account_code)
            if acct is None:
                return None
            return {"code": acct.code, "name": acct.name, "is_detail": acct.is_detail}

    te_session = session_factory()
    te_repo = ToolEquipmentRepo(te_session)
    te_alloc_repo = ToolEquipmentAllocationRepo(te_session)
    te_coa_adapter = _COAServiceAdapter(app.coa_service)  # type: ignore[attr-defined]
    te_svc = ToolEquipmentService(
        repo=te_repo,
        alloc_repo=te_alloc_repo,
        fy_service=app.fy_service,  # type: ignore[attr-defined]
        coa_service=te_coa_adapter,
    )
    te_alloc_engine = AllocationEngine(
        repo=te_repo,
        alloc_repo=te_alloc_repo,
        fy_service=app.fy_service,  # type: ignore[attr-defined]
        coa_service=te_coa_adapter,
    )
    init_tools_equipment_bp(te_svc, te_alloc_engine)

    from src.bricks.system_settings.storage import SQLAlchemyPeriodLockRepository

    init_settings_service(
        SystemSettingsService(
            SQLAlchemySystemSettingsRepository(session_factory()),
            SQLAlchemyPeriodLockRepository(session_factory()),
        )
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

    # ── Financial Statements ────────────────────────────────────────────
    from src.bricks.financial_statements.services import PeriodCloseService
    from src.bricks.financial_statements.web_adapter import (
        init_period_close_service,
        init_reports_ledger,
        reports_bp,
    )

    fs_repo = SQLAlchemyReportTemplateRepository(session_factory())
    fs_inst_repo = SQLAlchemyReportInstanceRepository(session_factory())
    fs_re_repo = SQLAlchemyRetainedEarningsRepository(session_factory())
    app.fs_template_repo = fs_repo  # type: ignore[attr-defined]
    app.fs_instance_repo = fs_inst_repo  # type: ignore[attr-defined]
    app.fs_re_repo = fs_re_repo  # type: ignore[attr-defined]

    class _PeriodLockAdapter:
        def __init__(self, repo):
            self._r = repo

        def is_period_locked(self, company_id, fiscal_year, period):
            return self._r.is_locked(company_id, fiscal_year, period)

        def lock_period(self, company_id, fiscal_year, period, actor, notes=None):
            return self._r.lock(company_id, fiscal_year, period, actor, notes=notes)

    _fs_lock_repo = SQLAlchemyPeriodLockRepository(session_factory())
    _period_close_svc = PeriodCloseService(period_lock=_PeriodLockAdapter(_fs_lock_repo))
    init_period_close_service(_period_close_svc)
    init_reports_ledger(ledger_source)
    app.register_blueprint(reports_bp)

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
