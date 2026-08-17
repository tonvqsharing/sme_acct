"""Infrastructure repository implementations (SQLAlchemy stubs)."""
from __future__ import annotations
import json
from datetime import date
from uuid import UUID
from sqlalchemy import func, select
from src.application.ports import (
    CompanyRepositoryPort,
    InvoiceRepositoryPort,
    PartnerRepositoryPort,
    VoucherRepositoryPort,
)
from src.domain.entities.company import AccountingRegime, BankAccount, Company
from src.domain.entities.contact import Partner
from src.domain.entities.invoice import Invoice, InvoiceStatus, InvoiceType
from src.domain.entities.voucher import AccountCode, DocumentType, Voucher, VoucherStatus
from src.domain.exceptions import AlreadyExistsError, DuplicateMSTError, NotFoundError
from src.infrastructure.database import db
from src.infrastructure.database.models import (
    AccountingRegimeEnum,
    BankAccountModel,
    CAListEntryModel,
    CompanyModel,
    CompanyStatusEnum,
    CompanyTypeEnum,
    DocumentTypeEnum,
    EntityTypeEnum,
    EInvoiceSeriesModel,
    FlagTypeEnum,
    InvoiceItemModel,
    InvoiceModel,
    InvoiceStatusEnum,
    InvoiceTypeEnum,
    PartnerModel,
    PeriodLockModel,
    VoucherLineModel,
    VoucherModel,
    VoucherStatusEnum,
)

class SQLAlchemyPartnerRepository(PartnerRepositoryPort):
    """Maps domain Partner <-> SQLAlchemy PartnerModel."""
    def create(self, partner: Partner) -> Partner:
        model = PartnerModel(
            code=partner.code,
            name=partner.name,
            tax_id=str(partner.tax_id) if partner.tax_id else None,
            entity_type=EntityTypeEnum(partner.entity_type.value),
            address=partner.address,
            phone=partner.phone,
            email=partner.email,
            tax_agency=partner.tax_agency,
            created_at=partner.created_at,
            updated_at=partner.updated_at,
        )
        db.session.add(model)
        db.session.commit()
        return self._to_domain(model)
    def get_by_id(self, partner_id: UUID) -> Partner | None:
        model = db.session.get(PartnerModel, partner_id)
        return self._to_domain(model) if model else None
    def get_by_code(self, code: str) -> Partner | None:
        stmt = select(PartnerModel).where(PartnerModel.code == code)
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None
    def list_active(self, page: int = 1, page_size: int = 20):
        stmt = (
            select(PartnerModel)
            .where(PartnerModel.is_active.is_(True))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        models = db.session.scalars(stmt).all()
        return [self._to_domain(m) for m in models]
    @staticmethod
    def _to_domain(model: PartnerModel) -> Partner:
        from src.domain.entities.contact import Partner as PartnerEntity
        return PartnerEntity(
            code=model.code,
            name=model.name,
            entity_type=model.entity_type.value,
            tax_id=model.tax_id,
            address=model.address,
            phone=model.phone,
            email=model.email,
            tax_agency=model.tax_agency,
        )

class SQLAlchemyInvoiceRepository(InvoiceRepositoryPort):
    """Maps Invoice domain entity <-> InvoiceModel."""
    def create(self, invoice: Invoice) -> Invoice:
        model = InvoiceModel(
            serial=invoice.serial,
            invoice_number=invoice.invoice_number,
            invoice_type=InvoiceTypeEnum(invoice.invoice_type.value),
            status=InvoiceStatusEnum(invoice.status.value),
            issue_date=invoice.issue_date,
            partner_id=invoice.partner_id,
            partner_name=invoice.partner_name,
            partner_tax_id=invoice.partner_tax_id,
            currency=invoice.currency,
            exchange_rate=invoice.exchange_rate,
            subtotal=invoice.subtotal,
            vat_total=invoice.vat_total,
            grand_total=invoice.grand_total,
            notes=invoice.notes,
            replaced_by_id=invoice.replaced_by_id,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )
        db.session.add(model)
        db.session.flush()
        for item in invoice.items:
            db.session.add(
                InvoiceItemModel(
                    invoice_id=model.id,
                    product_name=item.product_name,
                    unit=item.unit,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount=item.discount,
                    vat_rate=item.vat_rate.value,
                    vat_amount=item.vat_amount,
                    line_total=item.total_amount,
                )
            )
        db.session.commit()
        return self._to_domain(model)
    def get_by_id(self, invoice_id: UUID) -> Invoice | None:
        model = db.session.get(InvoiceModel, invoice_id)
        return self._to_domain(model) if model else None
    def list_by_partner(self, partner_id: UUID, page: int = 1, page_size: int = 20):
        stmt = (
            select(InvoiceModel)
            .where(InvoiceModel.partner_id == partner_id)
            .order_by(InvoiceModel.issue_date.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        models = db.session.scalars(stmt).all()
        return [self._to_domain(m) for m in models]
    @staticmethod
    def _to_domain(model: InvoiceModel) -> Invoice:
        from src.domain.entities.invoice import Invoice as InvoiceEntity
        from src.domain.entities.invoice import InvoiceItem, TaxRate
        invoice = InvoiceEntity(
            serial=model.serial,
            invoice_number=model.invoice_number,
            invoice_type=InvoiceType(model.invoice_type.value),
            partner_name=model.partner_name,
            partner_tax_id=model.partner_tax_id,
            partner_id=model.partner_id,
            issue_date=model.issue_date,
            notes=model.notes,
        )
        invoice.status = InvoiceStatus(model.status.value)
        invoice.subtotal = float(model.subtotal)
        invoice.vat_total = float(model.vat_total)
        invoice.grand_total = float(model.grand_total)
        for item in model.items or []:
            invoice.items.append(
                InvoiceItem(
                    product_name=item.product_name,
                    quantity=float(item.quantity),
                    unit_price=float(item.unit_price),
                    unit=item.unit,
                    vat_rate=TaxRate(item.vat_rate),
                    discount=float(item.discount),
                )
            )
        invoice._recalculate()
        return invoice

class SQLAlchemyVoucherRepository(VoucherRepositoryPort):
    """Maps Voucher domain entity <-> VoucherModel."""
    def create(self, voucher: Voucher) -> Voucher:
        model = VoucherModel(
            voucher_number=voucher.voucher_number,
            voucher_type=DocumentTypeEnum(voucher.voucher_type.value),
            status=VoucherStatusEnum(voucher.status.value),
            voucher_date=voucher.voucher_date,
            accounting_date=voucher.accounting_date,
            notes=voucher.notes,
            created_by_id=voucher.created_by,
        )
        db.session.add(model)
        db.session.flush()
        for line in voucher.lines:
            db.session.add(
                VoucherLineModel(
                    voucher_id=model.id,
                    account_code=str(line.account_code),
                    description=line.description,
                    debit=line.debit,
                    credit=line.credit,
                    cost_center=line.cost_center,
                    department=line.department,
                )
            )
        db.session.commit()
        return self._to_domain(model)
    def get_by_id(self, voucher_id: UUID) -> Voucher | None:
        model = db.session.get(VoucherModel, voucher_id)
        return self._to_domain(model) if model else None
    def get_by_number(self, voucher_number: str) -> Voucher | None:
        stmt = select(VoucherModel).where(VoucherModel.voucher_number == voucher_number)
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None
    def lock(self, voucher_id: UUID) -> Voucher:
        model = db.session.get(VoucherModel, voucher_id)
        if not model:
            raise NotFoundError(f"Voucher {voucher_id} not found")
        model.status = VoucherStatusEnum.LOCKED
        db.session.commit()
        return self._to_domain(model)
    @staticmethod
    def _to_domain(model: VoucherModel) -> Voucher:
        from src.domain.entities.voucher import Voucher as VoucherEntity
        from src.domain.entities.voucher import VoucherLine
        voucher = VoucherEntity(
            voucher_number=model.voucher_number,
            voucher_type=model.voucher_type.value,
            voucher_date=model.voucher_date,
            accounting_date=model.accounting_date,
            notes=model.notes,
        )
        voucher.status = VoucherStatus(model.status.value)
        voucher.created_by = model.created_by_id
        voucher.approved_by = model.approved_by_id
        return voucher

class SQLAlchemyCompanyRepository(CompanyRepositoryPort):
    """Maps Company domain entity <-> CompanyModel."""
    def create(self, company: Company) -> Company:
        existing = db.session.scalars(
            select(CompanyModel).where(CompanyModel.mst == str(company.mst))
        ).first()
        if existing:
            raise DuplicateMSTError(
                f"Mã số thuế '{company.mst}' đã được sử dụng bởi đơn vị '{existing.legal_name}'"
            )
        model = CompanyModel(
            legal_name=company.legal_name,
            mst=str(company.mst),
            headquarters_address=company.headquarters_address,
            legal_representative=company.legal_representative,
            business_reg_number=company.business_reg_number,
            business_reg_date=company.business_reg_date,
            business_fields=json.dumps(company.business_fields, ensure_ascii=False),
            company_type=CompanyTypeEnum(company.company_type.value),
            accounting_regime=AccountingRegimeEnum(company.accounting_regime.value),
            fiscal_year_start_month=company.fiscal_year_start_month,
            fiscal_year_start_day=company.fiscal_year_start_day,
            responsible_accountant_name=company.responsible_accountant_name,
            responsible_accountant_license=company.responsible_accountant_license,
            tax_agency=company.tax_agency,
            controlling_tax_office=company.controlling_tax_office,
            bhxh_code=company.bhxh_code,
            bhxh_agency=company.bhxh_agency,
            authorized_capital=company.authorized_capital,
            phone=company.phone,
            email=company.email,
            website=company.website,
            short_name=company.short_name,
            status=CompanyStatusEnum(company.status.value),
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at,
            created_by=company.created_by,
            updated_by=company.updated_by,
            config_version=company.config_version,
            legal_reviewed_at=company.legal_reviewed_at,
            legal_reviewed_by=company.legal_reviewed_by,
            mst_changed_at=company.mst_changed_at,
        )
        for acct in company.bank_accounts:
            model.bank_account_models.append(
                BankAccountModel(
                    bank_name=acct.bank_name,
                    account_number=acct.account_number,
                    account_holder=acct.account_holder,
                    branch=acct.branch,
                    is_primary=acct.is_primary,
                )
            )
        db.session.add(model)
        db.session.commit()
        return self._to_domain(model)
    def update(self, company: Company) -> Company:
        """Persist state changes to an existing company (matched by id)."""
        model = db.session.get(CompanyModel, company.id)
        if not model:
            raise NotFoundError(f"Company {company.id} not found")
        # Guard against MST collision with another company
        if model.mst != str(company.mst):
            existing = db.session.scalars(
                select(CompanyModel)
                .where(CompanyModel.mst == str(company.mst))
                .where(CompanyModel.id != company.id)
            ).first()
            if existing:
                raise DuplicateMSTError(
                    f"Mã số thuế '{company.mst}' đã được sử dụng bởi đơn vị '{existing.legal_name}'"
                )
        model.legal_name = company.legal_name
        model.mst = str(company.mst)
        model.headquarters_address = company.headquarters_address
        model.legal_representative = company.legal_representative
        model.fiscal_year_start_month = company.fiscal_year_start_month
        model.fiscal_year_start_day = company.fiscal_year_start_day
        model.responsible_accountant_name = company.responsible_accountant_name
        model.responsible_accountant_license = company.responsible_accountant_license
        model.tax_agency = company.tax_agency
        model.controlling_tax_office = company.controlling_tax_office
        model.bhxh_code = company.bhxh_code
        model.bhxh_agency = company.bhxh_agency
        model.authorized_capital = company.authorized_capital
        model.phone = company.phone
        model.email = company.email
        model.website = company.website
        model.short_name = company.short_name
        model.status = CompanyStatusEnum(company.status.value)
        model.is_active = company.is_active
        model.config_version = company.config_version
        model.legal_reviewed_at = company.legal_reviewed_at
        model.legal_reviewed_by = company.legal_reviewed_by
        model.mst_changed_at = company.mst_changed_at
        model.updated_at = company.updated_at
        model.updated_by = company.updated_by
        # Replace bank accounts
        db.session.query(BankAccountModel).filter(BankAccountModel.company_id == model.id).delete(
            synchronize_session=False
        )
        for acct in company.bank_accounts:
            db.session.add(
                BankAccountModel(
                    company_id=model.id,
                    bank_name=acct.bank_name,
                    account_number=acct.account_number,
                    account_holder=acct.account_holder,
                    branch=acct.branch,
                    is_primary=acct.is_primary,
                )
            )
        db.session.commit()
        return self._to_domain(model)
    def get_by_id(self, company_id: UUID) -> Company | None:
        model = db.session.get(CompanyModel, company_id)
        return self._to_domain(model) if model else None
    def get_by_mst(self, mst: str) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.mst == mst)
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None
    def get_active(self) -> Company | None:
        stmt = (
            select(CompanyModel)
            .where(CompanyModel.is_active.is_(True))
            .where(CompanyModel.status == CompanyStatusEnum.ACTIVE)
            .order_by(CompanyModel.created_at.desc())
        )
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None
    def list_active(self, page: int = 1, page_size: int = 20) -> list[Company]:
        stmt = (
            select(CompanyModel)
            .where(CompanyModel.is_active.is_(True))
            .order_by(CompanyModel.created_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        models = db.session.scalars(stmt).all()
        return [self._to_domain(m) for m in models]
    def _get_bank_accounts(self, model: CompanyModel) -> list[BankAccount]:
        return [
            BankAccount(
                bank_name=ba.bank_name,
                account_number=ba.account_number,
                account_holder=ba.account_holder,
                branch=ba.branch,
                is_primary=ba.is_primary,
            )
            for ba in (model.bank_account_models or [])
        ]
    def _to_domain(self, model: CompanyModel) -> Company:
        from src.domain.entities.base import TaxId
        from src.domain.entities.company import (
            Company as CompanyEntity,
        )
        from src.domain.entities.company import (
            CompanyStatus,
            CompanyType,
        )
        bf = []
        if model.business_fields:
            try:
                bf = json.loads(model.business_fields)
            except (json.JSONDecodeError, TypeError):
                bf = []
        return CompanyEntity(
            legal_name=model.legal_name,
            mst=TaxId(model.mst),
            headquarters_address=model.headquarters_address,
            legal_representative=model.legal_representative,
            business_reg_number=model.business_reg_number,
            business_reg_date=model.business_reg_date,
            business_fields=bf,
            company_type=CompanyType(model.company_type.value),
            accounting_regime=AccountingRegime(model.accounting_regime.value),
            fiscal_year_start_month=model.fiscal_year_start_month,
            fiscal_year_start_day=model.fiscal_year_start_day,
            responsible_accountant_name=model.responsible_accountant_name,
            responsible_accountant_license=model.responsible_accountant_license,
            tax_agency=model.tax_agency,
            controlling_tax_office=model.controlling_tax_office,
            bhxh_code=model.bhxh_code,
            bhxh_agency=model.bhxh_agency,
            authorized_capital=float(model.authorized_capital),
            phone=model.phone,
            email=model.email,
            website=model.website,
            short_name=model.short_name,
            bank_accounts=self._get_bank_accounts(model),
            status=CompanyStatus(model.status.value),
            is_active=model.is_active,
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            config_version=model.config_version,
            legal_reviewed_at=model.legal_reviewed_at,
            legal_reviewed_by=model.legal_reviewed_by,
            mst_changed_at=model.mst_changed_at,
        )
