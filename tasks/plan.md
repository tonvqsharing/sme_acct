# Implementation Plan: XML Invoice Ingest v2 (TT91/2026)

## Overview
Parse Vietnamese e-invoice XML files (TT91/2026 format) and auto-create `SupplierInvoice` records. Handles VAT invoices (mau so 1), sales invoices (mau so 2), and other types per Appendix I symbol system. Integrates with existing `PurchaseService.create_invoice` gates.

## Architecture Decisions
- XML parsing: `xml.etree.ElementTree` (stdlib, no new deps)
- New brick: `src/bricks/xml_ingest/` — separates parsing concern from purchase domain
- Parser is pure Python (domain layer) — no Flask/SQLAlchemy imports
- Service layer calls `PurchaseService.create_invoice` for gate enforcement
- Duplicate guard: `exists_duplicate()` already on repository port

## Task List

### Phase 1: Domain — XML parser

#### Task 1: TT91 invoice symbol parser
Parse 6-char invoice symbol string into structured data (coded/uncoded, year, type, internal code).

**Acceptance criteria:**
- [ ] `InvoiceSymbol` dataclass with fields: is_coded, year, type_code, internal_code
- [ ] `parse_symbol("1C26TAA")` returns correct breakdown
- [ ] `parse_symbol("1K26TYY")` returns correct breakdown
- [ ] Invalid symbols raise `ValueError`

**Files:** `src/bricks/xml_ingest/domain.py`
**Scope:** S (1 file)

#### Task 2: XML field mapping constants
Define XPath expressions for TT91 XML invoice fields per Appendix III templates.

**Acceptance criteria:**
- [ ] Constants for seller info (name, MST, address)
- [ ] Constants for buyer info (name, MST, address)
- [ ] Constants for invoice lines (item name, quantity, unit price, amount, VAT rate)
- [ ] Constants for invoice header (number, symbol, date, type)

**Files:** `src/bricks/xml_ingest/domain.py`
**Scope:** S (1 file)

#### Task 3: XML invoice parser
Parse TT91-format XML into `ParsedInvoice` dataclass.

**Acceptance criteria:**
- [ ] `ParsedInvoice` dataclass with all fields from SupplierInvoice
- [ ] `parse_xml_invoice(xml_bytes: bytes) -> ParsedInvoice`
- [ ] Handles VAT invoice lines with amount + VAT
- [ ] Handles invoice symbol decomposition
- [ ] Invalid XML raises descriptive errors

**Files:** `src/bricks/xml_ingest/domain.py`
**Scope:** M (1 file, complex logic)

### Phase 2: Service — ingest orchestration

#### Task 4: XMLIngestService
Orchestrate XML parse → domain validation → PurchaseService.create_invoice.

**Acceptance criteria:**
- [ ] `ingest_single(xml_bytes, company_id, actor_id) -> SupplierInvoice`
- [ ] Calls `parse_xml_invoice` then `PurchaseService.create_invoice`
- [ ] Duplicate check: returns existing invoice if `exists_duplicate` matches
- [ ] Propagates gate errors (PERIOD_CLOSED, INVALID_ACCOUNT, etc.)

**Files:** `src/bricks/xml_ingest/services.py`
**Scope:** S (1 file)

#### Task 5: Batch ingest
Support multiple XML files in one call.

**Acceptance criteria:**
- [ ] `ingest_batch(xml_list, company_id, actor_id) -> list[IngestResult]`
- [ ] Each result has `status` (created/duplicate/error) + `invoice_id` or `error`
- [ ] Partial failures don't abort batch

**Files:** `src/bricks/xml_ingest/services.py`
**Scope:** S (extend service)

### Phase 3: Web adapter — API endpoints

#### Task 6: Single XML upload endpoint
POST `/api/v1/purchase-invoices/ingest` with XML file upload.

**Acceptance criteria:**
- [ ] Accepts `multipart/form-data` with XML file
- [ ] Returns created `SupplierInvoice` (201) or duplicate (409)
- [ ] Validates content-type is XML
- [ ] WRITE_ROLES required

**Files:** `src/bricks/purchases/web_adapter.py`
**Scope:** S (1 file)

#### Task 7: Batch XML upload endpoint
POST `/api/v1/purchase-invoices/ingest-batch` with multiple XML files.

**Acceptance criteria:**
- [ ] Accepts multiple XML files in single request
- [ ] Returns per-file results (created/duplicate/error)
- [ ] WRITE_ROLES required

**Files:** `src/bricks/purchases/web_adapter.py`
**Scope:** S (1 file)

### Phase 4: Tests

#### Task 8: Unit tests — domain parser
Test invoice symbol parsing, XML field extraction, ParsedInvoice construction.

**Acceptance criteria:**
- [ ] Test all 9 template codes (1-9)
- [ ] Test C/K coded/uncoded
- [ ] Test year extraction
- [ ] Test valid XML parse
- [ ] Test invalid XML handling
- [ ] Test missing required fields

**Files:** `tests/unit/xml_ingest/`
**Scope:** M (multiple test cases)

#### Task 9: Unit tests — service layer
Test ingest orchestration with mock PurchaseService.

**Acceptance criteria:**
- [ ] Test single ingest success
- [ ] Test duplicate detection
- [ ] Test gate error propagation
- [ ] Test batch with mixed results

**Files:** `tests/unit/xml_ingest/`
**Scope:** M

#### Task 10: Integration tests — API endpoints
Test XML upload endpoints with real app.

**Acceptance criteria:**
- [ ] Test POST single XML → 201
- [ ] Test POST duplicate → 409
- [ ] Test POST invalid XML → 422
- [ ] Test POST batch → 200 with results
- [ ] Test unauthenticated → 401

**Files:** `tests/integration/test_xml_ingest_api.py`
**Scope:** M

### Checkpoint: Complete
- [ ] All tests pass
- [ ] Quality gates pass (ruff, black, mypy)
- [ ] AGENTS.md updated

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| TT91 XML schema varies by provider | High | Map common fields first; accept optional extras |
| Large XML files cause memory issues | Low | Stream parse if needed; start with full parse |
| PurchaseService gates too strict for batch | Medium | Log failures per-file, continue batch |

## Legal Reference
- Thông tư 91/2026/TT-BTC (eff 01/07/2026)
- Phụ lục I: Invoice symbol system
- Phụ lục III: Data transfer templates (01/TH-HĐĐT)
- NĐ 254/2026/NĐ-CP Art 10: Invoice content requirements
