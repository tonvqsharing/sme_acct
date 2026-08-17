# Code Quality – Code Convention – Code Style

## 1. Tổng quan

### Mục tiêu
1. Thống nhất cách viết code.
2. Nâng cao chất lượng, giảm defect.
3. Giảm chi phí review code.
4. Onboard người mới nhanh.
5. Áp dụng trực tiếp, không giáo điều.

### Phạm vi áp dụng
- Toàn bộ codebase: backend Python/Flask, frontend JS/Tailwind, SQL, CI.
- Không áp dụng kiến trúc tổng thể (đã có tài liệu riêng), chỉ tập trung vào **cách viết code**.

### Đối tượng áp dụng
- Team 3–10 engineers, trình độ mixed (senior + mid).
- Mọi PR đều phải pass trước khi merge.

### Nguyên tắc cốt lõi
- **Tự động hóa trước, tranh luận sau.** Linter/formatter quyết định; human chỉ giải quyết edge case.
- **MUST > SHOULD > MAY.** Bắt buộc trước, khuyến nghị sau, tùy chọn cuối.
- **Pragmatic over perfect.** Chọn quy tắc dễ áp dụng, không chọn quy tắc "đẹp" nhưng tốn chi phí.
- **Domain trước, framework sau.** Domain layer không phụ thuộc Flask/SQLAlchemy.

---

## 2. Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                  CODE QUALITY FRAMEWORK                      │
├──────────────┬──────────────┬───────────────────────────────┤
│  CODE STYLE  │   CONVENTION │        CODE QUALITY           │
│ (Định dạng)  │  (Tổ chức)   │       (Thiết kế)              │
├──────────────┼──────────────┼───────────────────────────────┤
│ • black      │ • Clean      │ • Unit tests (domain)         │
│ • Prettier   │   Arch       │ • Integration tests (API)     │
│ • ruff       │ • REST API   │ • Static analysis             │
│ • 4 spaces   │ • Error      │ • Security basics             │
│ • snake_case │   handling   │ • Performance (N+1, paginate) │
│ • line=100   │ • Logging    │ • Anti-patterns               │
│              │ • Commits    │                               │
└──────────────┴──────────────┴───────────────────────────────┘
         ↓                ↓                    ↓
         └────────────────┼────────────────────┘
                          ↓
                  Maintainable Software
                          ↓
                  Happy Engineering Team
```

---

## 3. Code Style

Mục tiêu: Đọc code không cần đoán định dạng. Formatter giải quyết; human không tranh cãi.

### 3.1 Quy tắc đặt tên

| Loại | Quy tắc | Ví dụ đúng | Ví dụ sai |
|------|---------|------------|-----------|
| File Python | `snake_case.py` | `partner_service.py` | `PartnerService.py`, `partnerService.py` |
| Class | `PascalCase` | `PartnerService` | `partner_service`, `Partner` (OK), `partnerManager` |
| Function/Variable | `snake_case` | `create_partner()`, `total_amount` | `createPartner()`, `totalAmount` |
| Constant | `UPPER_SNAKE_CASE` | `VAT_RATE = 10`, `TOLERANCE = 0.01` | `vat_rate`, `VatRate` |
| Module/JS | `kebab-case.js` | `invoice-modal.js` | `invoiceModal.js` |
| CSS class | `kebab-case` (Tailwind utility) | `bg-red-500` | `bgRed500` |

**MUST:** Tên biến phải tiếng Anh, có nghĩa rõ ràng. Không dùng `temp`, `data`, `info`, `obj` nếu có thể đặt tên cụ thể hơn.

### 3.2 Định dạng code

| Thuộc tính | Quy tắc |
|------------|---------|
| Indent Python | 4 spaces, không dùng tab |
| Indent JS/CSS | 2 spaces |
| Line length | 100 characters (theo black config) |
| Blank lines | 2 giữa top-level definitions, 1 giữa methods |
|Trailing whitespace | Không được có |
| Semicolon Python | Không dùng, trừ khi code trên cùng một dòng |

**Tự động hóa:** `black` (Python) + `prettier` (JS/CSS). Không có ngoại lệ.

### 3.3 Import order

Python: stdlib → third-party → local. `ruff` sẽ tự động sắp xếp (I rule).

```python
# ĐỤNG
import os
import sys
from flask import Flask
from src.domain.entities.partner import Partner
```

### 3.4 Comment và Documentation

- **MUST:** Comment giải thích **WHY**, không phải **WHAT**.
- **MUST:** Không comment-out code. Xóa luôn. Git có lịch sử.
- **SHOULD:** Docstring cho mọi public function/class. Ngắn gọn: mô tả 1 dòng, rồi Args/Returns/Raises.

```python
# ĐÚNG
def post_voucher(voucher_id: UUID, approved_by: UUID) -> Voucher:
    """Đăng chứng từ sổ kế toán.

    Args:
        voucher_id: Chứng từ cần đăng.
        approved_by: Người duyệt.

    Raises:
        InvalidVoucher: Nếu chứng từ không cân bằng hoặc không ở trạng thái DRAFT.
    """
    ...

# SAI
def pv(vid, ab):
    # post voucher
    ...
```

---

## 4. Code Convention

Mục tiêu: Team đọc code của nhau như đọc chung một dự án.

### 4.1 Cấu trúc thư mục

```
project-root/
├── src/                          # Một package duy nhất
│   ├── domain/                   # Core business logic, PURE PYTHON
│   │   ├── entities/             # Aggregate roots + entities
│   │   ├── value_objects/        # TaxId, AccountCode, Money
│   │   ├── exceptions/           # Domain exceptions
│   │   └── repositories/         # Ports (abc.ABC)
│   ├── application/              # Use cases / Service orchestration
│   │   ├── services/             # Business workflow stubs
│   │   └── ports/                # Interface definitions (re-export)
│   ├── infrastructure/           # External concerns
│   │   ├── database/
│   │   │   ├── __init__.py       # db = SQLAlchemy()
│   │   │   └── models.py         # SQLAlchemy 2.0 models
│   │   └── repositories/         # SQLAlchemyRepo adapters
│   └── presentation/             # UI/API layer
│       ├── api/                  # REST blueprints
│       ├── ui/                   # HTML blueprints
│       ├── forms/                # WTForms
│       └── serializers/          # Domain → JSON
├── tests/                        # Mirror src/ structure
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/                   # Alembic (flask db)
├── static/                       # Frontend assets
├── templates/                    # Jinja2 HTML
├── config/                       # Environment configs
├── docs/                         # Documentation
├── app.py                        # Entrypoint (factory)
└── pyproject.toml                # Single source of truth
```

**MUST:** Tuân thủ Clean Architecture. Domain layer **không** được import `flask`, `sqlalchemy`, hoặc bất kỳ framework nào.

**MUST:** Khi thêm enum mới, thêm vào **cả** `src/domain/entities/base.py` **và** `src/infrastructure/database/models.py`. Hai nơi phải sync.

### 4.2 API Quy ước

| Aspect | Quy tắc |
|--------|---------|
| Base path | `/api/v1/` |
| Resource naming | Plural noun, lowercase: `/partners`, `/invoices`, `/vouchers` |
| JSON keys | `snake_case`, tiếng Anh |
| Error messages | Tiếng Việt, ngắn gọn |
| Success response | `{"data": ..., "pagination": {...}}` |
| Error response | `{"error": "Mô tả lỗi", "code": "ERROR_CODE"}` |
| HTTP verbs | GET (read), POST (create), PUT/PATCH (update), DELETE (remove) |
| Status codes | 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Server Error |

### 4.3 Xử lý lỗi

```python
# ĐÚNG: Domain raise → Service handle → Presentation translate
# Domain
raise NotFoundError("Không tìm thấy đối tượng")

# Service
try:
    ...
except DomainException:
    raise  # Re-raise, không transform thành generic Exception

# Presentation (Flask route)
@app.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e), "code": "NOT_FOUND"}), 404
```

**MUST:** Không catch `Exception` trừ khi có log + re-raise hoặc xử lý rõ ràng.
**MUST:** Không swallow error (pass trong except).

### 4.4 Logging

- **MUST:** Dùng `logging` module. **Cấm** `print()` trong production code.
- **SHOULD:** Structured log: `logger.info("msg", extra={"key": value})`
- **MAY:** Thêm `request_id` vào log nếu có middleware request ID.

```python
import logging
logger = logging.getLogger(__name__)

# ĐÚNG
logger.info("Creating partner", extra={"code": partner.code})

# SAI
print(f"Creating partner {partner.code}")
```

### 4.5 Validation

- **MUST:** Domain layer validate business rules (TaxId regex, AccountCode regex).
- **MUST:** Presentation layer validate request format (WTForms/Marshmallow).
- **SHOULD:** Fail fast — validate ngay đầu hàm, không để logic chạy sâu rồi mới báo lỗi.

### 4.6 Commit message

**MUST:** Theo [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(invoice): add VAT calculation for credit notes
fix(partner): handle null tax_id gracefully
docs(api): document error response schema
chore(deps): upgrade Flask to 3.1.3
refactor(voucher): extract balance check to method
test(partner): add unit tests for TaxId validation
```

Body: Giải thích **WHY** (nếu không rõ từ subject). Không giải thích **WHAT** (code diff đã nói).

### 4.7 Branch naming

```
feature/INV-001-add-invoice-api
bugfix/PARTNER-002-tax-id-validation
hotfix/SECURITY-003-disable-talisman-debug
refactor/VOUCHER-004-extract-balance-check
```

## 5. Code Quality

### 5.1 Đọc trước, viết sau
- Code đọc nhiều hơn viết. Ưu tiên rõ ràng hơn ngắn gọn.
- **MUST:** Tránh "clever" code. Người đ maintain 6 tháng sau có thể là bạn.

### 5.2 Hàm ngắn, trách nhiệm rõ

| Metric | Quy tắc |
|--------|---------|
| Độ dài lý tưởng | < 30 lines |
| Độ dài chấp nhận | < 50 lines |
| Độ dài tối đa | < 80 lines (hard limit) |
| Số tham số | < 5 (nếu nhiều hơn, dùng `dataclass` hoặc `**kwargs`) |
| Mức độ trừu tượng | Mỗi hàm một abstraction level |

```python
# ĐÚNG: Ngắn, rõ mục đích
def create_partner(self, *, code: str, name: str, entity_type: str) -> Partner:
    if self.partner_repo.get_by_code(code):
        raise AlreadyExistsError(...)
    return self.partner_repo.create(Partner(...))

# SAI: Quá dài, làm nhiều việc
def process_partner_and_generate_report_and_send_email(...):
    ...
```

### 5.3 DRY (Don't Repeat Yourself)

- **SHOULD:** Trích xuất hàm khi copy-paste ≥ 3 lần.
- **MUST:** Không trích xuất sớm. Duplication rõ ràng tốt hơn abstraction sai.
- **Ở đâu:** Business logic trong `src/domain/` hoặc `src/application/`. Không để duplicate ở presentation layer.

### 5.4 Anti-pattern cấm
- ❌ Magic number: `if status == 3:` → `if status == InvoiceStatus.DRAFT:`
- ❌ God object: Một class làm mọi thứ
- ❌ Shotgun surgery: Một thay đổi phải sửa 10 chỗ
- ❌ Silent catch: `except: pass`
- ❌ Global mutable state: Trừ khi config singleton đã approved

### 5.5 Error handling

```python
# ĐÚNG: Catch specific, log, re-raise nếu cần
try:
    invoice.post()
except InvalidInvoice as exc:
    logger.error("Invalid invoice", extra={"id": invoice.id})
    raise  # Presentation layer sẽ bắt và trả JSON

# SAI: Catch-all, swallow
try:
    invoice.post()
except Exception:
    pass
```

### 5.6 Null/Empty handling

- **MUST:** Dùng `Optional[T]` typing rõ ràng.
- **MUST:** Kiểm tra `None`/rỗng ngay đầu hàm (guard clause).
- **SHOULD:** Dùng `assert` cho điều kiện "không bao giờ xảy ra" trong dev.

```python
# ĐÚNG
def get(self, partner_id: UUID) -> Partner:
    partner = self.partner_repo.get_by_id(partner_id)
    if not partner:
        raise NotFoundError(f"Không tìm thấy đối tượng {partner_id}")
    return partner
```

### 5.7 Test tối thiểu

| Loại | Phạm vi |覆盖率 mục tiêu |
|------|---------|----------------|
| Unit test | Domain entities + services | 80% |
| Integration test | API endpoints (POST/GET) | Mỗi endpoint có ít nhất 1 happy path |
| Edge case | TaxId validation, Invoice calc, Voucher balance | MUST cover |

**MUST:** Mỗi PR phải đi kèm test cho logic mới/sửa.
**SHOULD:** Test đặt tên rõ: `test_create_partner_should_raise_when_code_exists()`.

### 5.8 Bảo mật cơ bản

| Risk | Quy tắc |
|------|---------|
| SQL Injection | Dùng SQLAlchemy ORM. **Cấm** raw string concat trong query. |
| CSRF | Bật Flask-WTF CSRF protection. Form HTML phải có token. |
| Secrets | **Cấm** hardcode key/secret/password. Dùng env vars. |
| Input validation | Validate ở domain boundary. Không tin input từ client. |
| HTTPS | Dùng `Flask-Talisman` khi `DEBUG=False`. Local dev: `DEBUG=1`. |

### 5.9 Performance cơ bản

- **MUST:** Phân trang cho list endpoints (20–50 items/page).
- **MUST:** Tránh N+1 query. Dùng `selectinload`/`joinedload` khi cần.
- **SHOULD:** Index các trường hay search/filter (`partner.code`, `invoice.serial`).

---

## 6. Quy tắc bắt buộc / khuyến nghị / tùy chọn

| ID | Quy tắc | Mức độ |
|----|---------|--------|
| CS-01 | File Python dùng `snake_case.py` | MUST |
| CS-02 | Class dùng `PascalCase` | MUST |
| CS-03 | Function/variable dùng `snake_case` | MUST |
| CS-04 | Constant dùng `UPPER_SNAKE_CASE` | MUST |
| CS-05 | Line length 100 chars | MUST |
| CS-06 | Python indent 4 spaces, JS/CSS 2 spaces | MUST |
| CS-07 | Chạy `black` + `prettier` trước commit | MUST |
| CS-08 | Không dùng `print()`, dùng `logging` | MUST |
| CS-09 | Comment giải thích WHY, không WHAT | MUST |
| CS-10 | Xóa code dead, không comment-out | MUST |
| CC-01 | Domain layer không import Flask/SQLAlchemy | MUST |
| CC-02 | Tuân theo cấu trúc thư mục Clean Arch | MUST |
| CC-03 | Sync enum giữa domain và infrastructure | MUST |
| CC-04 | API dùng `/api/v1/`, plural, snake_case keys | MUST |
| CC-05 | Error message tiếng Việt, field names tiếng Anh | MUST |
| CC-06 | Domain raise exception, Presentation translate HTTP | MUST |
| CC-07 | Không catch `Exception` trừ khi log + handle | MUST |
| CC-08 | Commit theo Conventional Commits | MUST |
| CC-09 | Branch: `type/ISSUE-ID-description` | MUST |
| CC-10 | Mỗi PR cần ít nhất 1 reviewer approve | MUST |
| CQ-01 | Hàm < 50 lines (ideal), < 80 lines (max) | MUST |
| CQ-02 | Unit test domain + integration test API | MUST |
| CQ-03 | Coverage ≥ 80% (CI enforce) | SHOULD |
| CQ-04 | Không magic number trong business logic | MUST |
| CQ-05 | Guard clause cho None/empty | SHOULD |
| CQ-06 | SQLAlchemy ORM, không raw SQL string concat | MUST |
| CQ-07 | Pagination cho list endpoints | MUST |
| CQ-08 | Input validation ở domain boundary | MUST |
| CQ-09 | Dependencies pin version trong pyproject.toml | MUST |
| CQ-10 | Secrets trong env, không hardcode | MUST |
| CQ-11 | Dùng `uv` để quản lý dependencies | MUST |
| CQ-12 | UTF-8 encoding, ISO 8601 date format | MUST |
| CQ-13 | Descriptive naming, tránh `temp`, `data`, `foo` | SHOULD |
| CQ-14 | Hàm 1 thư mục trừu tượng (no mixed levels) | SHOULD |
| CQ-15 | Log level phù hợp: INFO flow, ERROR exception | SHOULD |

---

## 7. Ví dụ tốt / xấu

### 7.1 Domain Entity

```python
# ĐÚNG: Immutable value object, validation rõ ràng
@dataclass(frozen=True)
class TaxId:
    value: str

    def __post_init__(self):
        cleaned = self.value.replace("-", "").strip()
        if not re.match(r"^\d{10}(-\d{3})?$", self.value):
            raise ValueError("Mã số thuế không hợp lệ")
        object.__setattr__(self, "value", cleaned)

# SAI: Validation lỏng lẻo, mutable không kiểm soát
class TaxId:
    def __init__(self, value):
        self.value = value  # Accept anything
```

### 7.2 Service Layer

```python
# ĐÚNG: Single responsibility, rõ ràng
class PartnerService:
    def create_partner(self, *, code: str, name: str) -> Partner:
        if self.repo.get_by_code(code):
            raise AlreadyExistsError(...)
        return self.repo.create(Partner(code=code, name=name))

# SAI: Logical tách rời, khó test
class PartnerService:
    def do_everything(self, data):
        # 200 lines: validate + create + send email + generate report + ...
```

### 7.3 Error Handling

```python
# ĐÚNG
try:
    invoice.post()
except InvalidInvoice as exc:
    logger.error("Invalid invoice", extra={"id": invoice.id})
    raise  # Let Flask errorhandler deal with it

# SAI
try:
    invoice.post()
except:
    return {"error": "Something went wrong"}  # 500 mà không biết lý do
```

---

## 8. Code Review Checklist

Dùng checklist này trong mỗi PR review. Checkbox ngắn, không dài dòng.

**Tự động (CI phải pass):**
- [ ] `ruff check` passed
- [ ] `black --check` passed
- [ ] `mypy` passed
- [ ] `pytest` passed
- [ ] Coverage ≥ 80%

**Thủ công (Reviewer check):**
- [ ] **Architecture:** Domain layer có import Flask/SQLAlchemy không? (MUST NOT)
- [ ] **Naming:** Tên có nghĩa rõ không? Không có `temp`/`data`?
- [ ] **Function size:** Hàm > 80 lines? (Nếu có, yêu cầu tách)
- [ ] **Error handling:** Có bare `except:` không? Có swallow error không?
- [ ] **Security:** Có hardcode secret không? SQL có an toàn không? CSRF có bật không?
- [ ] **Business logic:** Nằm đúng layer không? (Domain/Application, không phải Presentation)
- [ ] **Test:** Logic mới/sửa có test không? Test có ý nghĩa không?
- [ ] **Logging:** Có log quan trọng không? Dùng `logging`, không phải `print()`
- [ ] **Docs:** Docstring/comments có cập nhật không?
- [ ] **Commit:** Message rõ ràng, theo Conventional Commits?

---

## 9. Công cụ đề xuất

### 9.1 Đã có trong dự án

| Tool | Mục đích | Command |
|------|----------|---------|
| `black` | Format Python | `black src tests` |
| `ruff` | Lint Python | `ruff check src tests` |
| `mypy` | Type check | `mypy src` |
| `pytest` | Test runner | `pytest tests/` |
| `prettier` | Format JS/CSS | `prettier --write static/ templates/` |
| `Flask-Talisman` | Security headers | Auto khi `DEBUG=0` |

### 9.2 CI Pipeline đơn giản

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install uv
      - run: uv pip install --python=.venv/bin/python -e .[dev]
      - run: ruff check src tests
      - run: black --check src tests
      - run: mypy src
      - run: pytest tests/ --cov=src --cov-report=xml
```

### 9.3 Pre-commit hooks (tùy chọn)

Nếu team muốn cứng hơn, dùng `pre-commit` framework:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks: [{ id: black }]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [{ id: ruff }]
```

---

## 10. Anti-pattern phổ biến (cần tránh)

| Anti-pattern | Vấn đề | Cách tránh |
|--------------|--------|-----------|
| God Class/Service | Khó test, khó maintain | Chia nhỏ theo use case |
| Shotgun Surgery | Một đổi 10 file | Group related logic |
| Anemic Domain | Business logic nằm ở Service, Entity chỉ là data bag | Đặt business rule trong Entity |
| Lava Flow | Dead code accumulate | Xóa không dùng, refactor thường xuyên |
| Magic Numbers | Không hiểu ý nghĩa số | Extract `VAT_RATE`, `TOLERANCE` |
| Cargo Cult | Copy pattern mà không hiểu | Chỉ dùng pattern khi giải quyết vấn đề thực tế |
| Premature Optimization | Phức tạp code cho performance chưa chắc xảy ra | Profile trước, đơn giản trước |

---

## 11. Tài liệu tham khảo

- PEP 8 – Style Guide for Python Code: https://peps.python.org/pep-0008/
- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/en/20/
- Conventional Commits: https://www.conventionalcommits.org/
- OWASP Top 10 (bảo mật web): https://owasp.org/www-project-top-ten/
- Clean Architecture (Robert C. Martin) – tham khảo khái niệm, không áp dụng giáo điều.
- [CẦN XÁC NHẬN] SonarQube quality gate rules – cần config phù hợp với Python 3.11.

---

## 12. Phụ lục: Quick Reference

```
Khi viết code mới:
  1. Tạo file theo naming convention (snake_case.py)
  2. Đặt class/function theo quy tắc tên
  3. Viết logic trong đúng layer (Domain/App/Infra/Presentation)
  4. Chạy black + ruff trước khi commit
  5. Viết test tương ứng
  6. Commit message: type(scope): description

Khi review code:
  1. CI pass chưa?
  2. Architecture đúng chưa?
  3. Test có ý nghĩa không?
  4. Có security risk không?
  5. Có magic number không?
```

---

*Tài liệu này được maintain bởi team. Mọi đề xuất thay đổi tạo PR và review bởi ít nhất 1 senior.*