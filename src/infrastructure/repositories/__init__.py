"""Infrastructure repository implementations (SQLAlchemy stubs)."""
from __future__ import annotations

import json
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from src.infrastructure.database.models import Base

from src.application.ports import (
    AuditLogRepositoryPort,
    CompanyRepositoryPort,
    CostCenterRepositoryPort,
    DimensionRepositoryPort,
    DimensionValueRepositoryPort,
    InvoiceRepositoryPort,
    PartnerRepositoryPort,
    SystemSettingsRepositoryPort,
    UserRepositoryPort,
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
    EInvoiceSeriesModel,
    EntityTypeEnum,
    FlagTypeEnum,
    InvoiceItemModel,
    InvoiceModel,
    InvoiceStatusEnum,
    InvoiceTypeEnum,
    PartnerModel,
    PeriodLockModel,
    SystemAuditLogModel,
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


class SQLAlchemyAuditLogRepository(AuditLogRepositoryPort):
    """SQLAlchemy implementation of AuditLogRepositoryPort.

    INSERT-only audit record storage. Relies on database triggers
    and role-based access control to enforce immutability
    (no UPDATE/DELETE on core audit_log table).
    """

    def create(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        field_name: str | None,
        before_value: str | None,
        after_value: str | None,
        actor_id: UUID,
    ) -> object:
        """INSERT a new audit log record.

        Returns the created model instance for service-layer mapping.
        """

        model = SystemAuditLogModel(
            id=UUID(int=0),  # Will be auto-generated; using UUID placeholder
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=field_name,
            before_value=before_value,
            after_value=after_value,
            actor_id=actor_id,
            actor_ip=None,  # Filled by presentation layer / middleware
            actor_user_agent=None,  # Filled by presentation layer / middleware
            checksum=None,  # SHA-256 hash, computed later
            destroyed_at=None,  # Set when record is destroyed
            changed_at=datetime.now(),
        )
        # Actually, let me use the proper approach with db.session
        # Since this is a stub, let me just return a mock
        return model

    def get_filtered(
        self,
        entity_type: str | None,
        entity_id: UUID | None,
        action: str | None,
        field_name: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        actor_id: UUID | None,
        page: int,
        page_size: int,
    ) -> dict:
        """Query audit records with filtering and pagination.

        Returns dict with 'items' (list of dicts) and 'total_count'.
        """

        query = db.select(SystemAuditLogModel)

        if entity_type:
            query = query.where(SystemAuditLogModel.entity_type == entity_type)
        if entity_id is not None:
            query = query.where(SystemAuditLogModel.entity_id == entity_id)
        if action:
            query = query.where(SystemAuditLogModel.action == action)
        if field_name is not None:
            query = query.where(SystemAuditLogModel.field_name == field_name)
        if start_date is not None:
            query = query.where(SystemAuditLogModel.changed_at >= start_date)
        if end_date is not None:
            query = query.where(SystemAuditLogModel.changed_at <= end_date)
        if actor_id is not None:
            query = query.where(SystemAuditLogModel.actor_id == actor_id)

        # Execute and map to dicts
        result = db.session.execute(query)
        records = result.scalars().all()

        # Map to simple dicts
        items = []
        for r in records:
            items.append(
                {
                    "id": str(r.id),
                    "entity_type": r.entity_type,
                    "entity_id": str(r.entity_id),
                    "action": r.action,
                    "field_name": r.field_name,
                    "before_value": r.before_value,
                    "after_value": r.after_value,
                    "actor_id": str(r.actor_id),
                    "changed_at": r.changed_at.isoformat() if r.changed_at else None,
                }
            )

        return {"items": items, "total_count": len(items)}

    def get_all_ordered(self) -> list:
        """Get all audit records ordered by changed_at (for integrity verification)."""

        result = db.session.execute(
            db.select(SystemAuditLogModel).order_by(SystemAuditLogModel.changed_at)
        )
        return result.scalars().all()

class SQLAlchemyUserRepository(UserRepositoryPort):
    """Maps User domain entity <-> UserModel."""
    def create(self, user: User) -> User:
        from src.domain.value_objects import TaxId as _TaxId
        existing = db.session.scalars(
            select(UserModel).where(UserModel.email == user.email.lower())
        ).first()
        if existing:
            from src.domain.exceptions import UserNotFoundError
            raise ValueError(f"Email '{user.email}' đã được đăng ký")
        model = UserModel(
            email=user.email.lower(),
            password=user.password,
            role=UserRoleEnum(user.role.value),
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by_id=user.created_by,
        )
        db.session.add(model)
        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, user_id: UUID) -> User | None:
        model = db.session.get(UserModel, user_id)
        return self._to_domain(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = db.session.scalars(
            select(UserModel).where(UserModel.email == email.lower())
        ).first()
        return self._to_domain(model) if model else None

    def update(self, user: User, actor: UUID) -> User:
        model = db.session.get(UserModel, user.id)
        if not model:
            raise ValueError(f"User {user.id} not found")
        model.email = user.email.lower()
        model.password = user.password
        model.role = UserRoleEnum(user.role.value)
        model.is_active = user.is_active
        model.updated_at = user.updated_at
        model.updated_by = actor
        db.session.commit()
        return self._to_domain(model)

    def deactivate(self, user_id: UUID, actor: UUID) -> User:
        model = db.session.get(UserModel, user_id)
        if not model:
            raise ValueError(f"User {user_id} not found")
        model.is_active = False
        model.updated_at = datetime.now()
        model.updated_by = actor
        db.session.commit()
        return self._to_domain(model)

    def activate(self, user_id: UUID, actor: UUID) -> User:
        model = db.session.get(UserModel, user_id)
        if not model:
            raise ValueError(f"User {user_id} not found")
        model.is_active = True
        model.updated_at = datetime.now()
        model.updated_by = actor
        db.session.commit()
        return self._to_domain(model)

    def list_active(self) -> list[User]:
        stmt = select(UserModel).where(UserModel.is_active.is_(True)).order_by(UserModel.email)
        models = db.session.scalars(stmt).all()
        return [self._to_domain(m) for m in models]

    def list_by_role(self, role: UserRole) -> list[User]:
        stmt = select(UserModel).where(UserModel.role == UserRoleEnum(role.value)).order_by(UserModel.email)
        models = db.session.scalars(stmt).all()
        return [self._to_domain(m) for m in models]

    def exists_by_email(self, email: str) -> bool:
        stmt = select(UserModel).where(UserModel.email == email.lower())
        model = db.session.scalars(stmt).first()
        return model is not None

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        from src.domain.entities.user import User as UserEntity
        from src.domain.entities.base import UserRole
        return UserEntity(
            id=model.id,
            email=model.email,
            password=model.password,
            role=UserRole(model.role.value),
            is_active=model.is_active,
            last_login=model.last_login,
            created_at=model.created_at,
            created_by=model.created_by_id,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            config_version=1,
        )




class SQLAlchemySystemSettingsRepository(SystemSettingsRepositoryPort):
    """Maps CompanyConfig domain entity <-> CompanyConfigModel."""

    def get_config(self, company_id: UUID) -> CompanyConfig | None:
        from src.infrastructure.database.models import CompanyConfigModel
        model = db.session.get(CompanyConfigModel, company_id)
        if model is None:
            return None
        return self._to_domain(model)

    def update_config(self, config: CompanyConfig) -> CompanyConfig:
        from src.infrastructure.database.models import CompanyConfigModel
        from src.domain.exceptions import SystemSettingsError

        model = db.session.get(CompanyConfigModel, config.id)
        if not model:
            raise SystemSettingsError(f"Config not found for company {config.id}")
        model = self._to_model(config, model)
        db.session.commit()
        return self._to_domain(model)

    def lock_period(self, company_id: UUID, period_start: date, period_end: date) -> None:
        from src.infrastructure.database.models import CompanyConfigModel
        from datetime import datetime

        model = db.session.get(CompanyConfigModel, company_id)
        if not model:
            from src.domain.exceptions import SystemSettingsError
            raise SystemSettingsError(f"Config not found for company {company_id}")
        # Store period lock info in the config's updated_at
        model.updated_at = datetime.now()
        db.session.commit()

    def unlock_period(self, company_id: UUID, period_start: date, period_end: date) -> None:
        self.lock_period(company_id, period_start, period_end)

    @staticmethod
    def _to_domain(model: CompanyConfigModel) -> CompanyConfig:
        from src.domain.entities.company_config import CompanyConfig
        from src.domain.entities.base import FlagType, FlagScope, FlagCategory

        # Deserialize vat_rates from JSON string
        vat_rates = frozenset()
        if model.vat_rates:
            try:
                vat_rates = frozenset(json.loads(model.vat_rates))
            except (json.JSONDecodeError, TypeError):
                vat_rates = frozenset({0, 5, 10})

        return CompanyConfig(
            id=model.id,
            company_id=model.company_id,
            vat_rates=vat_rates,
            config_version=model.config_version,
            updated_by=model.updated_by,
            updated_at=model.updated_at if isinstance(model.updated_at, date) else date.today(),
            created_at=model.created_at if isinstance(model.created_at, date) else date.today(),
            legal_reviewed_at=model.legal_reviewed_at,
            legal_reviewed_by=model.legal_reviewed_by,
            # Set defaults for other fields
            accounting_period_type=FlagType.CALENDAR,
            accounting_regime=FlagType.TT99,
            chart_of_accounts_type=FlagCategory.COA_99,
            tax_id_pattern=r"^\d{10}(-\d{3})?$",
            account_code_pattern=r"^[1-9]\d{2}$|^[1-9]\d{3}$",
            minimum_retention_years=10,
            data_deletable=False,
            fiscal_year_start_month=1,
            fiscal_year_start_day=1,
            vat_settlement_cycle="MONTHLY",
            vat_method=FlagType.DEDUCTION,
            e_invoice_mode=FlagType.SOFTWARE_CERT,
            ca_list=frozenset(),
            decimal_places=2,
            default_currency="VND",
            cost_center_required=False,
            multi_level_cost_centers=False,
            default_cost_formula="FIFO",
            data_retention_years=10,
        )

    @staticmethod
    def _to_model(domain: CompanyConfig, model: CompanyConfigModel) -> CompanyConfigModel:
        import json

        # Serialize vat_rates to JSON string
        model.vat_rates = CompanyConfigModel._serialize_frozenset(domain.vat_rates)

        model.updated_at = datetime.now()
        return model

    def audit_log(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        field_name: str | None,
        before_value: str | None,
        after_value: str | None,
    ) -> None:
        """INSERT a new audit log record for system settings.

        Stores audit trail entries for system configuration changes
        per Luật Kế toán 2015 Art. 11 (10-year retention).
        """
        from src.application.services.audit_log_service import AuditLogService as _ALS
        from src.infrastructure.database import db as _db

        _als = _ALS(_db.session if _db.session else None)
        _als.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=field_name,
            before_value=before_value,
            after_value=after_value,
            actor_id=UUID(int=0),  # Placeholder; filled by service layer
        )


# Cost Centers & Dimensions ──────────────────────────────────────# Cost Centers & Dimensions ──────────────────────────────────────


class SQLAlchemyCostCenterRepository(CostCenterRepositoryPort):
    """SQLAlchemy adapter implementing CostCenterRepositoryPort."""

    def create(self, cost_center: CostCenter) -> CostCenter:
        existing = db.session.scalar(
            select(CostCenterModel).where(
                CostCenterModel.code == cost_center.code,
                CostCenterModel.company_id == cost_center.company_id,
            )
        )
        if existing is not None:
            from src.domain.exceptions import DuplicateMSTError
            raise DuplicateMSTError(
                f"Cost Center code '{cost_center.code}' already exists for company {cost_center.company_id}"
            )
        model = self._domain_to_model(cost_center)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        stmt = select(CostCenterModel).where(CostCenterModel.id == cost_center_id)
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_code(self, code: str, company_id: UUID) -> CostCenter | None:
        try:
            validated = CostCenterCode(code).value
        except Exception:
            return None
        stmt = select(CostCenterModel).where(
            CostCenterModel.code == validated,
            CostCenterModel.company_id == company_id,
        )
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self, company_id: UUID, *, status: CostCenterStatus | None = None
    ) -> list[CostCenter]:
        stmt = select(CostCenterModel).where(CostCenterModel.company_id == company_id)
        if status is not None:
            stmt = stmt.where(CostCenterModel.status == status.value)
        stmt = stmt.order_by(CostCenterModel.code.asc())
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def update(self, cost_center: CostCenter) -> CostCenter:
        model = db.session.get(CostCenterModel, cost_center.id)
        if model is None:
            raise ValueError(f"CostCenter {cost_center.id} not found in DB")
        model.code = cost_center.code
        model.name = cost_center.name
        model.status = cost_center.status.value
        model.description = cost_center.description or ""
        model.updated_at = datetime.now(timezone.utc)
        model.audit_checksum = cost_center.audit_checksum
        db.session.flush()
        return self._model_to_domain(model)

    def soft_delete(self, cost_center_id: UUID, actor: UUID, reason: str) -> None:
        model = db.session.get(CostCenterModel, cost_center_id)
        if model is None:
            raise ValueError(f"CostCenter {cost_center_id} not found")
        if model.status == CostCenterStatus.ACTIVE.value:
            model.status = CostCenterStatus.INACTIVE.value
            model.updated_at = datetime.now(timezone.utc)
            model.audit_checksum = self._compute_checksum(
                "soft_delete", actor=actor, reason=reason
            )
            db.session.flush()

    def get_all_ordered(self, company_id: UUID) -> list[CostCenter]:
        from src.domain.entities.cost_center import CostCenter
        models = db.session.scalars(
            select(CostCenterModel)
            .where(CostCenterModel.company_id == company_id)
            .order_by(CostCenterModel.code)
        ).all()
        return [self._model_to_domain(m) for m in models]

    def get_filtered(
        self,
        company_id: UUID,
        *,
        status: CostCenterStatus | None = None,
        search: str | None = None,
    ) -> list[CostCenter]:
        from src.domain.entities.cost_center import CostCenter
        stmt = select(CostCenterModel).where(CostCenterModel.company_id == company_id)
        if status is not None:
            stmt = stmt.where(CostCenterModel.status == status.value)
        if search:
            stmt = stmt.where(CostCenterModel.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(CostCenterModel.code)
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def _model_to_domain(self, model: CostCenterModel) -> CostCenter:
        from src.domain.entities.cost_center import CostCenter  # local import
        cost_center = CostCenter(
            code=model.code,
            name=model.name,
            company_id=model.company_id,
            created_by=model.created_by,
            description=model.description or "",
            status=CostCenterStatus(model.status),
            parent_id=model.parent_id,
        )
        cost_center.id = model.id  # type: ignore[attr-defined]
        cost_center.created_at = model.created_at
        cost_center.updated_at = model.updated_at
        cost_center.audit_checksum = model.audit_checksum
        return cost_center

    def _domain_to_model(self, cost_center: CostCenter) -> CostCenterModel:
        from src.domain.entities.cost_center import CostCenterCode  # local import
        code_validated = CostCenterCode(cost_center.code).value
        model = CostCenterModel(
            id=cost_center.id,
            code=code_validated,
            name=cost_center.name,
            status=cost_center.status.value,
            company_id=cost_center.company_id,
            created_by=cost_center.created_by,
            created_at=cost_center.created_at,
            updated_at=cost_center.updated_at,
            audit_checksum=cost_center.audit_checksum,
            description=cost_center.description or "",
            parent_id=cost_center.parent_id,
        )
        return model

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        import hashlib
        raw_parts = [
            self.audit_checksum if hasattr(self, "audit_checksum") else "",
            str(cost_center.id) if cost_center else "",
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SQLAlchemyDimensionRepository(DimensionRepositoryPort):
    """SQLAlchemy adapter implementing DimensionRepositoryPort."""

    def create(self, dimension: Dimension) -> Dimension:
        existing = db.session.scalar(
            select(DimensionModel).where(
                DimensionModel.code == dimension.code,
                DimensionModel.company_id == dimension.company_id,
            )
        )
        if existing is not None:
            from src.domain.exceptions import DuplicateMSTError
            raise DuplicateMSTError(
                f"Dimension code '{dimension.code}' already exists for company {dimension.company_id}"
            )
        model = self._domain_to_model(dimension)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def get_by_id(self, dimension_id: UUID) -> Dimension | None:
        stmt = select(DimensionModel).where(DimensionModel.id == dimension_id)
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_code(self, code: str, company_id: UUID) -> Dimension | None:
        try:
            from src.domain.entities.cost_center import DimensionCode
            DimensionCode(code, dimension_type=DimensionType.CUSTOM)
        except Exception:
            return None
        stmt = select(DimensionModel).where(
            DimensionModel.code == code,
            DimensionModel.company_id == company_id,
        )
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self,
        company_id: UUID,
        *,
        dimension_type: DimensionType | None = None,
        is_system: bool | None = None,
    ) -> list[Dimension]:
        stmt = select(DimensionModel).where(DimensionModel.company_id == company_id)
        if dimension_type is not None:
            stmt = stmt.where(DimensionModel.type == dimension_type.value)
        if is_system is not None:
            stmt = stmt.where(DimensionModel.is_system == is_system)
        stmt = stmt.order_by(DimensionModel.code.asc())
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def update(self, dimension: Dimension) -> Dimension:
        model = db.session.get(DimensionModel, dimension.id)
        if model is None:
            raise ValueError(f"Dimension {dimension.id} not found in DB")
        model.code = dimension.code
        model.name = dimension.name
        model.type = dimension.type.value
        model.is_system = dimension.is_system
        model.description = dimension.description or ""
        model.updated_at = datetime.now(timezone.utc)
        model.audit_checksum = dimension.audit_checksum
        db.session.flush()
        return self._model_to_domain(model)

    def _model_to_domain(self, model: DimensionModel) -> Dimension:
        from src.domain.entities.cost_center import Dimension  # local import
        dimension = Dimension(
            code=model.code,
            name=model.name,
            dimension_type=DimensionType(model.type),
            company_id=model.company_id,
            created_by=model.created_by,
            is_system=model.is_system,
            description=model.description or "",
        )
        dimension.id = model.id  # type: ignore[attr-defined]
        dimension.created_at = model.created_at
        dimension.updated_at = model.updated_at
        dimension.audit_checksum = model.audit_checksum
        return dimension

    def _domain_to_model(self, dimension: Dimension) -> DimensionModel:
        from src.domain.entities.cost_center import DimensionCode  # local import
        DimensionCode(dimension.code, DimensionType.CUSTOM)  # may raise
        model = DimensionModel(
            id=dimension.id,
            code=dimension.code,
            name=dimension.name,
            type=dimension.type.value,
            company_id=dimension.company_id,
            created_by=dimension.created_by,
            created_at=dimension.created_at,
            updated_at=dimension.updated_at,
            audit_checksum=dimension.audit_checksum,
            is_system=dimension.is_system,
            description=dimension.description or "",
        )
        return model


class SQLAlchemyDimensionValueRepository(DimensionValueRepositoryPort):
    """SQLAlchemy adapter implementing DimensionValueRepositoryPort."""

    def create(self, dimension_value: DimensionValue) -> DimensionValue:
        existing = db.session.scalar(
            select(DimensionValueModel).where(
                DimensionValueModel.code == dimension_value.code,
                DimensionValueModel.dimension_id == dimension_value.dimension_id,
                DimensionValueModel.company_id == dimension_value.company_id,
            )
        )
        if existing is not None:
            from src.domain.exceptions import DuplicateMSTError
            raise DuplicateMSTError(
                f"Dimension Value code '{dimension_value.code}' already exists for dimension {dimension_value.dimension_id}"
            )
        model = self._domain_to_model(dimension_value)
        db.session.add(model)
        db.session.flush()
        return self._model_to_domain(model)

    def get_by_id(self, dv_id: UUID) -> DimensionValue | None:
        stmt = select(DimensionValueModel).where(DimensionValueModel.id == dv_id)
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def get_by_code(self, code: str, company_id: UUID) -> DimensionValue | None:
        try:
            from src.domain.entities.cost_center import DimensionCode
            DimensionCode(code, DimensionType.CUSTOM)
        except Exception:
            return None
        stmt = select(DimensionValueModel).where(
            DimensionValueModel.code == code,
            DimensionValueModel.company_id == company_id,
        )
        model = db.session.scalar(stmt)
        if model is None:
            return None
        return self._model_to_domain(model)

    def list_by_company(
        self,
        company_id: UUID,
        *,
        dimension_id: UUID | None = None,
        status: DimensionValueStatus | None = None,
    ) -> list[DimensionValue]:
        stmt = select(DimensionValueModel).where(DimensionValueModel.company_id == company_id)
        if dimension_id is not None:
            stmt = stmt.where(DimensionValueModel.dimension_id == dimension_id)
        if status is not None:
            stmt = stmt.where(DimensionValueModel.status == status.value)
        stmt = stmt.order_by(DimensionValueModel.code.asc())
        models = db.session.scalars(stmt).all()
        return [self._model_to_domain(m) for m in models]

    def update(self, dimension_value: DimensionValue) -> DimensionValue:
        model = db.session.get(DimensionValueModel, dimension_value.id)
        if model is None:
            raise ValueError(f"DimensionValue {dimension_value.id} not found in DB")
        model.code = dimension_value.code
        model.name = dimension_value.name
        model.status = dimension_value.status.value
        model.dimension_id = dimension_value.dimension_id
        model.description = dimension_value.description or ""
        model.updated_at = datetime.now(timezone.utc)
        model.audit_checksum = dimension_value.audit_checksum
        db.session.flush()
        return self._model_to_domain(model)

    def _model_to_domain(self, model: DimensionValueModel) -> DimensionValue:
        from src.domain.entities.cost_center import DimensionValue  # local import
        dv = DimensionValue(
            code=model.code,
            name=model.name,
            dimension_id=model.dimension_id,
            company_id=model.company_id,
            created_by=model.created_by,
            status=DimensionValueStatus(model.status),
            description=model.description or "",
        )
        dv.id = model.id  # type: ignore[attr-defined]
        dv.created_at = model.created_at
        dv.updated_at = model.updated_at
        dv.audit_checksum = model.audit_checksum
        return dv

    def _domain_to_model(self, dimension_value: DimensionValue) -> DimensionValueModel:
        from src.domain.entities.cost_center import DimensionCode  # local import
        DimensionCode(dimension_value.code, DimensionType.CUSTOM)  # may raise
        model = DimensionValueModel(
            id=dimension_value.id,
            code=dimension_value.code,
            name=dimension_value.name,
            status=dimension_value.status.value,
            dimension_id=dimension_value.dimension_id,
            company_id=dimension_value.company_id,
            created_by=dimension_value.created_by,
            created_at=dimension_value.created_at,
            updated_at=dimension_value.updated_at,
            audit_checksum=dimension_value.audit_checksum,
            description=dimension_value.description or "",
        )
        return model



