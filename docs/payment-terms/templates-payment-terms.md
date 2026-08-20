# Templates — Payment Terms & Document Numbering Module

## 1. Overview

This document captures all Templates (TL) for the Payment Terms & Document Numbering module. Templates define the structural patterns, JSON schemas, form structures, report formats, and migration patterns used throughout the module. Following the same patterns as the Bank & Cash Accounts module (BRD/Specs/Use Cases/Processes all completed v1 2026-08-18).

---

## 2. JSON Schemas

### 2.1 PaymentTermCreateRequest JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "PaymentTermCreateRequest",
    "type": "object",
    "required": ["company_id", "name", "due_days", "interest_rate", "actor", "reason"],
    "properties": {
        "company_id": {
            "type": "string",
            "format": "uuid",
            "description": "Company UUID (FK → companies.id, tenant isolation)"
        },
        "name": {
            "type": "string",
            "pattern": "^[\\p{L}\\p{N} \\-\\./]{1,200}$",
            "maxLength": 200,
            "description": "Payment term name (e.g., \"Net 30\", \"Thanh toán 15 ngày\")"
        },
        "due_days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3650,
            "description": "Số ngày trả nợ (ví dụ: 30 cho Net 30, tối đa 3650 năm)"
        },
        "interest_rate": {
            "type": "number",
            "minimum": 0,
            "maxDecimal": 6,
            "description": "Lãi suất trễ thanh toán (VND), ví dụ: 0.00 hoặc 8.50"
        },
        "actor": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của người thực hiện (D11 SOD policy, bắt buộc cho mọi mutation)"
        },
        "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Lý do thực hiện (bắt buộc trên tất cả mutation endpoints)"
        }
    },
    "additionalProperties": false
}
```

### 2.2 PaymentTermUpdateRequest JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "PaymentTermUpdateRequest",
    "type": "object",
    "required": ["actor", "reason"],
    "properties": {
        "name": {
            "type": "string",
            "pattern": "^[\\p{L}\\p{N} \\-\\./]{1,200}$",
            "maxLength": 200,
            "description": "Tên payment term (optional khi update)"
        },
        "due_days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3650,
            "description": "Số ngày trả nợ (optional khi update)"
        },
        "interest_rate": {
            "type": "number",
            "minimum": 0,
            "maxDecimal": 6,
            "description": "Lãi suất trễ thanh toán (optional khi update)"
        },
        "is_default": {
            "type": "boolean",
            "description": "Đặt làm payment term mặc định (SOD required, chỉ CHIEF_ACCOUNTANT/ADMIN/DIRECTOR)"
        },
        "actor": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của người thực hiện (D11 SOD policy, bắt buộc)"
        },
        "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Lý do thực hiện (bắt buộc trên tất cả mutation endpoints)"
        }
    },
    "additionalProperties": false
}
```

### 2.3 DocumentNumberingSeriesCreateRequest JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "DocumentNumberingSeriesCreateRequest",
    "type": "object",
    "required": ["company_id", "prefix", "name", "actor", "reason"],
    "properties": {
        "company_id": {
            "type": "string",
            "format": "uuid",
            "description": "Company UUID (FK → companies.id, tenant isolation)"
        },
        "prefix": {
            "type": "string",
            "pattern": "^[A-Z]{2,}/$",
            "description": "Chỉ số serie theo GDT Circular 163/2020/TT-BTC Art. 10 (Ví dụ: \"HD/\", \"PN/\", \"CV/\")"
        },
        "name": {
            "type": "string",
            "pattern": "^[\\p{L}\\p{N} \\-\\./]{1,200}$",
            "maxLength": 200,
            "description": "Tên series (Ví dụ: \"Hóa đơn\", \"Phiếu thu\", \"Phiếu chi\")"
        },
        "max_sequences": {
            "type": "integer",
            "minimum": 1,
            "maximum": 999999,
            "default": 999999,
            "description": "Số lượng tối đa cho số tự động tăng (default: 999999)"
        },
        "actor": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của người thực hiện (D11 SOD policy, bắt buộc)"
        },
        "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Lý do thực hiện (bắt buộc trên tất cả mutation endpoints)"
        }
    },
    "additionalProperties": false
}
```

### 2.4 DocumentNumberingSeriesIncrementRequest JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "DocumentNumberingSeriesIncrementRequest",
    "type": "object",
    "required": ["actor", "reason", "series_id"],
    "properties": {
        "series_id": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của document numbering series"
        },
        "actor": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của người thực hiện (D11 SOD policy, bắt buộc)"
        },
        "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Lý do thực hiện (bắt buộc trên tất cả mutation endpoints)"
        }
    },
    "additionalProperties": false
}
```

### 2.5 AuditLogEntry JSON Schema (Read-Only)

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AuditLogEntry",
    "type": "object",
    "readOnly": true,
    "properties": {
        "id": {
            "type": "string",
            "format": "uuid",
            "description": "Audit log entry ID"
        },
        "entity_type": {
            "type": "string",
            "enum": ["payment_term", "document_numbering_series", "invoice"],
            "description": "Loại entity bị ảnh hưởng"
        },
        "entity_id": {
            "type": "string",
            "format": "uuid",
            "description": "ID của entity bị ảnh hưởng"
        },
        "action": {
            "type": "string",
            "enum": ["CREATE", "UPDATE", "DEACTIVATE", "ACTIVATE", "INCREMENT", "DEFAULT_REQUEST", "DEFAULT_APPROVE", "DEFAULT_REJECT", "ACTIVATE_REQUEST", "ACTIVATE_APPROVE", "ACTIVATE_REJECT"],
            "description": "Hành động được thực hiện"
        },
        "actor_uuid": {
            "type": "string",
            "format": "uuid",
            "description": "UUID của người thực hiện hành động"
        },
        "reason": {
            "type": "string",
            "description": "Lý do thực hiện (từ request body)"
        },
        "old_value": {
            "type": "json",
            "description": "Giá trị trước khi thay đổi (nếu applicable)"
        },
        "new_value": {
            "type": "json",
            "description": "Giá trị sau khi thay đổi (entity JSON)"
        },
        "checksum": {
            "type": "string",
            "pattern": "^[a-f0-9]{64}$",
            "description": "SHA-256 checksum cho chaining audit trail"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "Thời điểm thực hiện hành động (ISO 8601)"
        }
    },
    "additionalProperties": false
}
```

---

## 3. Form Structures (HTMX + Bulma)

### 3.1 Payment Term Creation Form

```html
<!-- partial: src/templates/partials/payment_term/create.html -->
<section class="section">
    <div class="container">
        <h1 class="title">Thanh toán: Tạo payment term mới</h1>
        
        <form id="payment-term-create-form" hx-post="/api/v1/payment-terms" hx-target="this" hx-swap="afterbegin">
            <div class="field">
                <label class="label">Doanh nghiệp</label>
                <input type="hidden" id="company-id" name="company_id" value="{{ company_id }}">
                <input type="text" disabled readonly class="input" value="{{ company_name }}" disabled>
            </div>
            
            <div class="field">
                <label class="label">Tên payment term</label>
                <input type="text" id="name" name="name" class="input" placeholder="Ví dụ: Net 30" required>
            </div>
            
            <div class="field">
                <label class="label">Số ngày trả nợ</label>
                <input type="number" id="due_days" name="due_days" class="input" min="1" max="3650" value="30" required>
                <small class="help-text">Mặc định là 30 ngày (Net 30).</small>
            </div>
            
            <div class="field">
                <label class="label">Lãi suất trễ thanh toán (VND)</label>
                <input type="number" id="interest_rate" name="interest_rate" class="input" min="0" step="0.0001" value="0.00">
                <small class="help-text">Lãi suất suất tính cho quádue. để trống bằng 0.00.</small>
            </div>
            
            <div class="field">
                <label class="label">Người thực hiện (UUID)</label>
                <input type="text" id="actor" name="actor" class="input" placeholder="UUID của người dùng hiện tại" required>
                <small class="help-text">Bắt buộc cho audit và SOD.</small>
            </div>
            
            <div class="field">
                <label class="label">Lý do</label>
                <textarea id="reason" name="reason" class="textarea" rows="3" placeholder="Lý do tạo payment term này" required></textarea>
            </div>
            
            <div class="field">
                <button type="submit" class="button is-primary">Tạo payment term</button>
                <button type="button" class="button" onclick="event.target.form.reset()">Huỷ</button>
            </div>
        </form>
    </div>
</section>
```

### 3.2 Payment Term Update Form

```html
<!-- partial: src/templates/partials/payment_term/update.html -->
<section class="section">
    <div class="container">
        <h1 class="title">Thanh toán: Cập nhật payment term</h1>
        
        <form id="payment-term-update-form" hx-patch="/api/v1/payment-terms/{{ term_id }}" hx-target="this" hx-swap="afterbegin">
            <input type="hidden" name="actor" value="{{ actor_uuid }}">
            <input type="hidden" name="reason" value="{{ update_reason }}">
            
            <div class="field">
                <label class="label">Tên payment term</label>
                <input type="text" id="name" name="name" class="input" value="{{ term_name }}" required>
            </div>
            
            <div class="field">
                <label class="label">Số ngày trả nợ</label>
                <input type="number" id="due_days" name="due_days" class="input" min="1" max="3650" value="{{ term_due_days }}" required>
            </div>
            
            <div class="field">
                <label class="label">Lãi suất trễ thanh toán</label>
                <input type="number" id="interest_rate" name="interest_rate" class="input" min="0" step="0.0001" value="{{ term_interest_rate }}">
            </div>
            
            <div class="field">
                <label class="label">Đặt làm payment term mặc định</label>
                <div class="checkbox">
                    <input type="checkbox" id="is_default" name="is_default" {{ "checked" if term_is_default else "" }}>
                    <label class="label"><small>SOD: Cần phê duyệt ACCOUNTANT nếu đang đổi default</small></label>
                </div>
            </div>
            
            <div class="field">
                <button type="submit" class="button is-primary">Cập nhật</button>
                <button type="button" class="button" onclick="event.target.form.reset()">Huỷ</button>
            </div>
        </form>
    </div>
</section>
```

### 3.3 Document Numbering Series Creation Form

```html
<!-- partial: src/templates/partials/document_numbering/create.html -->
<section class="section">
    <div class="container">
        <h1 class="title">Số hiệu tài liệu: Tạo series mới</h1>
        
        <form id="series-create-form" hx-post="/api/v1/document-numbering" hx-target="this" hx-swap="afterbegin">
            <div class="field">
                <label class="label">Doanh nghiệp</label>
                <input type="hidden" id="company-id" name="company_id" value="{{ company_id }}">
                <input type="text" disabled readonly class="input" value="{{ company_name }}" disabled>
            </div>
            
            <div class="field">
                <label class="label">Chỉ số serie (prefix)</label>
                <input type="text" id="prefix" name="prefix" class="input" pattern="^[A-Z]{2,}/$" title="Ví dụ: HD/, PN/" required>
                <small class="help-text">Theo GDT Circular 163/2020/TT-BTC: 2+ chữ hoa theo bởi /</small>
            </div>
            
            <div class="field">
                <label class="label">Tên series</label>
                <input type="text" id="name" name="name" class="input" placeholder="Ví dụ: Hóa đơn" required>
            </div>
            
            <div class="field">
                <label class="label">Số lượng tối đa</label>
                <input type="number" id="max_sequences" name="max_sequences" class="input" min="1" max="999999" value="999999">
                <small class="help-text">Mặc định: 999999. Tăng nếu cần số lượng lớn.</small>
            </div>
            
            <div class="field">
                <label class="label">Người thực hiện (UUID)</label>
                <input type="text" id="actor" name="actor" class="input" placeholder="UUID của người dùng hiện tại" required>
                <small class="help-text">Bắt buộc cho audit và SOD.</small>
            </div>
            
            <div class="field">
                <label class="label">Lý do</label>
                <textarea id="reason" name="reason" class="textarea" rows="3" placeholder="Lý do tạo series này" required></textarea>
            </div>
            
            <div class="field">
                <button type="submit" class="button is-primary">Tạo series</button>
                <button type="button" class="button" onclick="event.target.form.reset()">Huỷ</button>
            </div>
        </form>
    </div>
</section>
```

### 3.4 Invoice Creation Form (with Auto-Numbering)

```html
<!-- partial: src/templates/partials/invoice/create.html -->
<section class="section">
    <div class="container">
        <h1 class="title">Hóa đơn: Tạo mới</h1>
        
        <form id="invoice-create-form" hx-post="/api/v1/invoices" hx-target="this" hx-swap="afterbegin">
            <div class="field">
                <label class="label">Khách hàng</label>
                <input type="text" id="customer" name="customer" class="input" placeholder="Tên khách hàng" required>
            </div>
            
            <div class="field">
                <label class="label">Ngày phát hành</label>
                <input type="date" id="issue_date" name="issue_date" class="input" value="{{ today_date }}" required>
                <small class="help-text">Ngày xuất hóa đơn. Sử dụng để tính ngày đến hạn.</small>
            </div>
            
            <div class="field">
                <label class="label">Số tiền (VND)</label>
                <input type="number" id="amount" name="amount" class="input" min="0" step="1000" required>
            </div>
            
            <div class="field">
                <label class="label">Thuế VAT (%)</label>
                <input type="number" id="vat_rate" name="vat_rate" class="input" min="0" max="100" step="0.01" value="0.1" required>
            </div>
            
            <div class="field">
                <label class="label">Phương thức thanh toán</label>
                <select id="payment_term_id" name="payment_term_id" class="select" required>
                    <option value="">-- Chọn payment term --</option>
                    {% for term in payment_terms %}
                    <option value="{{ term.id }}" {{ "selected" if term.is_default else "" }}>
                        {{ term.name }} ({{ term.due_days }} ngày)
                    </option>
                    {% endfor %}
                </select>
                <small class="help-text">Payment term sẽ quyết định ngày đến hạn (due_date).</small>
            </div>
            
            <div class="field">
                <label class="label">Lý do</label>
                <textarea id="reason" name="reason" class="textarea" rows="3" placeholder="Lý do tạo hóa đơn này" required></textarea>
            </div>
            
            <div class="field">
                <button type="submit" class="button is-primary">Tạo hóa đơn</button>
                <button type="button" class="button" onclick="event.target.form.reset()">Huỷ</button>
            </div>
        </form>
        
        <!-- Auto-generated document number display -->
        <div id="generated-document-number" class="notification is-info" style="display: none;">
            <strong>Số hiệu tài liệu đã tạo:</strong> <span id="doc-number-value"></span>
        </div>
    </div>
</section>
```

---

## 4. Report Templates

### 4.1 Payment Term Configuration Report

**Format:** HTML table (Bulma-styled) or CSV export  
**Purpose:** Audit report for payment term configuration; 10-year retention compliance  

| Field | Description |
|-------|-------------|
| Report Title | Payment Term Configuration Report |
| Period | Generated at: {{generated_at}} |
| Company | {{company_name}} (ID: {{company_id}}) |
| Total Terms | {{total_terms}} |
| Default Term | {{default_term_name}} (due {{default_due_days}} days) |
| Terms Table Headers | ID, Name, Due Days, Interest Rate, Is Default, Status, Created At |
| Terms Table Rows | {{term_id}}, {{term_name}}, {{term_due_days}}, {{term_interest_rate}}, {{term_is_default}}, {{term_status}}, {{term_created_at}} |
| Audit Trail | {{total_audit_events}} events in audit_log (10-year retention) |
| Checksum Chain | SHA-256 chain verified: {{checksum_chain_valid}} |
| Generated By | {{actor_uuid}} |
| Generation Timestamp | {{timestamp}} |

**Usage:** 
- CHIEF_ACCOUNTANT or ACCOUNTANT generates for quarterly audit
- Stored in document management system with 10-year retention
- Checksum chain verified for tamper-evidence

---

### 4.2 Document Numbering Series Report

**Format:** HTML table (Bulma-styled) or CSV export  
**Purpose:** Audit report for document numbering series; GDT compliance verification  

| Field | Description |
|-------|-------------|
| Report Title | Document Numbering Series Report |
| Period | Generated at: {{generated_at}} |
| Company | {{company_name}} (ID: {{company_id}}) |
| Total Series | {{total_series}} |
| Active Series | {{active_series_count}} / 15 (GDT max) |
| Series Table Headers | ID, Prefix, Name, Next Sequence, Max Sequences, Is Active, Status, Created At |
| Series Table Rows | {{series_id}}, {{series_prefix}}, {{series_name}}, {{series_next_seq}}, {{series_max_seq}}, {{series_is_active}}, {{series_status}}, {{series_created_at}} |
| Sequence Gaps | {{gaps_detected}} (should be 0 for continuous numbering) |
| Audit Trail | {{total_audit_events}} events in audit_log (10-year retention) |
| Generated By | {{actor_uuid}} |
| Generation Timestamp | {{timestamp}} |

**GDT Compliance Notes:**
- Maximum 15 active series per company (Circular 163/2020/TT-BTC Art. 10)
- Prefix format: ^[A-Z]{2,}/$ (TT163 compliance)
- Sequence must be continuous (no gaps)
- All events logged with SHA-256 checksum

---

### 4.3 Invoice Document Numbering Report

**Format:** HTML table (Bulma-styled) or CSV export  
**Purpose:** Track document numbers issued; audit trail for issued invoices  

| Field | Description |
|-------|-------------|
| Report Title | Invoice Document Numbering Report |
| Period | Generated at: {{generated_at}} |
| Company | {{company_name}} (ID: {{company_id}}) |
| Report Period | From: {{start_date}} To: {{end_date}} |
| Invoices Table Headers | ID, Document Number, Customer, Amount, VAT, Total, Issue Date, Due Date, Payment Term |
| Invoices Table Rows | {{invoice_id}}, {{document_number}}, {{customer}}, {{amount}}, {{vat_rate}}, {{total_amount}}, {{issue_date}}, {{due_date}}, {{payment_term_name}} |
| Total Invoices | {{total_invoices}} |
| Series Used | {{series_prefixes_used}} (unique prefixes across invoices) |
| Audit Trail | {{total_audit_events}} events in audit_log (10-year retention) |
| Generated By | {{actor_uuid}} |
| Generation Timestamp | {{timestamp}} |

**Usage:**
- Monthly/quarterly report for internal audit
- VAT finalization reporting
- Document number continuity verification
- Stored with 10-year retention per Luật Kế toán 2015 Art. 11

---

## 5. Migration Templates

### 5.1 Database Migration Template (Alembic/Flask-Migrate)

**File:** `migrations/versions/a1b2c3d4e5f6_payment_terms_module.py`

```python
"""Payment Terms & Document Numbering Module

Revision ID: a1b2c3d4e5f6
Revises: previous_revision_id
Create Date: 2026-08-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    # 1. Create payment_terms table
    op.create_table(
        'payment_terms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('due_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('interest_rate', sa.Numeric(precision=18, scale=6), nullable=False, server_default='0.00'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='payment_term_status'), nullable=False, server_default='ACTIVE'),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False, server_default=sa.text('date(\'now\')')),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'name', name='uq_payment_term_name_per_company'),
        sa.UniqueConstraint('company_id', 'is_default', name='uq_default_payment_term_per_company',
                           postgresql_where=sa.text('is_default = TRUE')),
    )
    op.create_index('ix_payment_terms_company_id', 'payment_terms', ['company_id'])
    
    # 2. Create document_numbering_series table
    op.create_table(
        'document_numbering_series',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('prefix', sa.String(length=20), nullable=False),
        sa.Column('next_sequence', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE'),
        sa.Column('max_sequences', sa.Integer(), nullable=False, server_default='999999'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='series_status'), nullable=False, server_default='ACTIVE'),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False, server_default=sa.text('date(\'now\')')),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'prefix', name='uq_series_prefix_per_company'),
        sa.UniqueConstraint('company_id', 'is_active', name='uq_active_series_per_company',
                           postgresql_where=sa.text('is_active = TRUE')),
    )
    op.create_index('ix_document_numbering_series_company_id', 'document_numbering_series', ['company_id'])
    
    # 3. Add payment_term_id FK to invoices table (if not exists)
    # Check if column exists before adding
    op.add_column('invoices', sa.Column('payment_term_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_invoices_payment_term', 'invoices', 'payment_terms', ['payment_term_id'], ['id'])
    
    # 4. Create initial audit log entries for module creation
    # (handled by audit_log_service.append_event in application code)
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    
    # 1. Drop foreign key and column from invoices
    op.drop_constraint('fk_invoices_payment_term', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'payment_term_id')
    
    # 2. Drop document_numbering_series table
    op.drop_table('document_numbering_series')
    
    # 3. Drop payment_terms table
    op.drop_table('payment_terms')
    
    # ### end Alembic commands ###
```

### 5.2 Seed Data Template (Optional Initial Data)

**File:** `scripts/seed/payment_terms_seed.py` (optional, for demo/prod deployment)

```python
"""Seed data for Payment Terms & Document Numbering module.

Optional seed data for initial deployment. Run after migration upgrade.
"""
from src.application.services.payment_term_service import PaymentTermService
from src.application.services.document_numbering_series_service import DocumentNumberingSeriesService
from src.domain.entities.payment_term import PaymentTerm
from src.domain.entities.document_numbering_series import DocumentNumberingSeries
from datetime import date

# Default payment terms for common Vietnamese business terms
DEFAULT_PAYMENT_TERMS = [
    PaymentTerm(
        name="Net 30",
        due_days=30,
        interest_rate=0.00,
        is_default=True,  # First one becomes default per company
        status="ACTIVE"
    ),
    PaymentTerm(
        name="Net 45",
        due_days=45,
        interest_rate=0.00,
        is_default=False,
        status="ACTIVE"
    ),
    PaymentTerm(
        name="Net 60",
        due_days=60,
        interest_rate=0.00,
        is_default=False,
        status="ACTIVE"
    ),
    PaymentTerm(
        name="Thanh toán 15 ngày",
        due_days=15,
        interest_rate=0.00,
        is_default=False,
        status="ACTIVE"
    ),
    PaymentTerm(
        name="Thanh toán sau 1 tháng",
        due_days=30,
        interest_rate=0.00,
        is_default=False,
        status="ACTIVE"
    ),
]

# Default document numbering series (typically 1 series per company for primary doc type)
DEFAULT_SERIES = [
    DocumentNumberingSeries(
        prefix="HD/",  # Hóa đơn - invoices
        name="Hóa đơn",
        max_sequences=999999,
        is_active=True,
        status="ACTIVE"
    ),
    DocumentNumberingSeries(
        prefix="PN/",  # Phiếu thu - receipts
        name="Phiếu thu",
        max_sequences=999999,
        is_active=False,  # Inactive by default; activate when first receipt issued
        status="INACTIVE"
    ),
    DocumentNumberingSeries(
        prefix="PC/",  # Phiếu chi - payments
        name="Phiếu chi",
        max_sequences=999999,
        is_active=False,  # Inactive by default; activate when first payment issued
        status="INACTIVE"
    ),
]

# Seed execution (run after migration):
# 1. Create default payment terms per company
# 2. Create default numbering series per company
# 3. Set first payment term as default (SOD: requires 2-actor approval in production)
```

---

## 6. API Response Templates

### 6.1 Payment Term Create Response (201)

```json
{
    "id": "c1234567-89ab-cdef-0123-456789abcdef",
    "company_id": "c1234567-89ab-cdef-0123-456789abcdef",
    "name": "Net 30",
    "due_days": 30,
    "interest_rate": 0.00,
    "is_default": false,
    "status": "ACTIVE",
    "created_at": "2026-08-20",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### 6.2 Payment Term Update Response (200)

```json
{
    "id": "c1234567-89ab-cdef-0123-456789abcdef",
    "company_id": "c1234567-89ab-cdef-0123-456789abcdef",
    "name": "Net 30 Updated",
    "due_days": 30,
    "interest_rate": 0.00,
    "is_default": true,
    "status": "ACTIVE",
    "created_at": "2026-08-20",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### 6.3 Document Numbering Series Create Response (201)

```json
{
    "id": "d1234567-89ab-cdef-0123-456789abcdef",
    "company_id": "c1234567-89ab-cdef-0123-456789abcdef",
    "prefix": "HD/",
    "next_sequence": 1,
    "is_active": true,
    "max_sequences": 999999,
    "status": "ACTIVE",
    "created_at": "2026-08-20",
    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### 6.4 Document Numbering Series Increment Response (200)

```json
{
    "document_number": "HD/000001",
    "next_sequence": 1,
    "series_id": "d1234567-89ab-cdef-0123-456789abcdef",
    "new_next_sequence": 1
}
```

### 6.5 Error Response Templates

**400 Missing Actor/Reason:**
```json
{
    "error": "actor là bắt buộc",
    "code": "MISSING_ACTOR"
}
```

**409 Duplicate Name:**
```json
{
    "error": "Tên đã tồn tại cho doanh nghiệp này",
    "code": "DUPLICATE_PAYMENT_TERM"
}
```

**422 Invalid Prefix Format:**
```json
{
    "error": "Định dạng prefix không hợp lệ theo GDT",
    "code": "INVALID_SERIES_PREFIX"
}
```

**409 Max Series Exceeded:**
```json
{
    "error": "Đã đạt giới hạn 15 series active cho doanh nghiệp này",
    "code": "MAX_SERIES_EXCEEDED"
}
```

**403 AUDITOR Read-Only:**
```json
{
    "error": "AUDITOR chỉ đọc",
    "code": "AUDITOR_READ_ONLY"
}
```

---