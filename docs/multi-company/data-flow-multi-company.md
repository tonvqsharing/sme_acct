# Data Flows — Multi-Company / Master-Module
> v0.1 | Status: DRAFT | Derives from: docs/brd-multi-company.md, docs/specs-multi-company.md

---

## DF-001: Subsidiary Invoice Posting Data Flow

```
[Subsidiary Bookkeeper UI]
  → POST /api/invoices {company_id, items...}
  → API layer: validate user has role for company_id
  → InvoiceService.post()
  → Domain Invoice.add_item() → recalculates subtotal/VAT/grand_total
  → InvoiceRepository.save()
  → DB: INSERT INTO invoices (company_id=...)
  → DB: INSERT INTO invoice_items (invoice_id=...)
  → EventBus.publish("InvoicePosted", {company_id, invoice_id, period})
  → [Subsidiary bookkeeper sees confirmation]
```

### Data touched:
| Table | Operation | company_id |
|---|---|---|
| invoices | INSERT | Required |
| invoice_items | INSERT | Inherited |
| partners | SELECT (scoped) | Filtered |
| audit_log | INSERT | Inherited |

---

## DF-002: Period Close Data Flow

```
[Subsidiary Bookkeeper]
  → POST /api/periods/close {company_id, period}
  → PeriodService.close_period()
  → 1. Check all vouchers balanced (Voucher.is_balanced())
  → 2. Check all invoices POSTED (not DRAFT)
  → 3. Generate TrialBalance snapshot
  → TBRepository.save_snapshot(company_id, period, trial_balance_json)
  → PeriodLockRepository.create({company_id, period, locked_by, locked_at})
  → EventBus.publish("PeriodClosed", {company_id, period})
  → NotificationService.notify_group_cfo(company_id, "TB available")
  → [Master CFO receives notification]
```

### Data touched:
| Table | Operation | Notes |
|---|---|---|
| periods | INSERT (lock) | Immutable once created |
| trial_balance_snapshots | INSERT | JSON blob of TB |
| vouchers | SELECT (validate) | Must all be balanced |
| invoices | SELECT (validate) | Must all be POSTED |
| notifications | INSERT | To GROUP_CFO |

---

## DF-003: Consolidation Run Data Flow

```
[GROUP_CFO]
  → POST /api/consolidation/runs {group_id, period_start, period_end}
  → ConsolidationService.initiate_run()
  → 1. Validate all group companies locked for period
  → 2. CREATE consolidation_runs (status=DRAFT)
  → 3. FOR each company in group:
        tb = TBRepository.get_snapshot(company_id, period)
        ConsolidationTBRepository.add_company_tb(run_id, tb)
  → 4. Return combined trial balance preview
  → [CFO reviews combined TB]

[CFO adds adjusting entries]
  → POST /api/consolidation/runs/{id}/entries {debit, credit, ...}
  → ConsolidationRunService.add_entry()
  → ConsolidationRun.recalculate_totals()

[CFO approves]
  → POST /api/consolidation/runs/{id}/approve
  → 1. Validate entries balanced (±0.01)
  → 2. UPDATE consolidation_runs SET status=POSTED
  → 3. INSERT INTO bctc_consolidated (run_id, bctc_json)
  → 4. EventBus.publish("ConsolidationPosted", {run_id})
  → 5. NotificationService.notify_auditors(run_id)
  → [Auditors can now view]
```

### Data touched:
| Table | Operation | Notes |
|---|---|---|
| consolidation_runs | INSERT → UPDATE | Status transition: DRAFT → POSTED |
| consolidation_tb_snapshots | INSERT | Per company, immutable |
| consolidation_adjusting_entries | INSERT | Linked to run |
| bctc_consolidated | INSERT | Final BCTC output |
| audit_log | INSERT | Every state change |

---

## DF-004: Intercompany Invoice Matching Data Flow

```
[Subsidiary A Bookkeeper]
  → POST /api/invoices {company_id=A, counterpart_mst=company_B_MST, is_intercompany=true}
  → InvoiceService.validate_intercompany(counterpart_mst)
  → CompanyRepository.get_by_mst(counterpart_mst) → returns company B
  → InvoiceRepository.save() with is_intercompany=True, related_company_id=B
  → EventBus.publish("IntercompanyInvoiceCreated", {from_company=A, to_company=B})

[Consolidation Run]
  → ConsolidationService.find_intercompany_pairs(run_id, period)
  → Query: SELECT * FROM invoices WHERE is_intercompany=True AND period=?
  → Group by (from_company, to_company, period)
  → Present pairs to CFO for elimination
  → CFO adds NST/NLD entry
  → [See DF-003 for approval flow]
```

### Data touched:
| Table | Operation | Notes |
|---|---|---|
| invoices | INSERT | Flagged `is_intercompany=True` |
| intercompany_matches | INSERT (or derived) | Derived from invoice pairs |
| consolidation_adjusting_entries | INSERT | Elimination entries |

---

## DF-005: User Authentication & Company Scoping Data Flow

```
[User Login]
  → POST /api/auth/login {email, password}
  → AuthService.authenticate()
  → Returns: {user_id, roles, assigned_company_ids}
  → Frontend stores in session
  → Frontend shows company switcher (if user has >1 company)

[Every API Request]
  → Request includes X-Company-Id header or session default
  → AuthMiddleware:
      1. Get user from session
      2. Get company_id from header/session
      3. Verify user has role for company_id
      4. If not → 403
  → Repository layer: all queries include WHERE company_id = ?
  → No cross-company data leakage possible at query level
```

### Data touched:
| Table | Operation | Notes |
|---|---|---|
| user_company_roles | SELECT | Determines access |
| * (all transactional) | WHERE company_id = ? | Mandatory filter |

---

## DF-006: Consolidated BCTC Generation (Report Data Flow)

```
[Consolidation Run POSTED]
  → BCTCReportService.generate(run_id)
  → 1. Fetch combined TB from consolidation_tb_snapshots
  → 2. Apply adjusting entries from consolidation_adjusting_entries
  → 3. Map accounts to BCTC line items per Circular 99/2025 Mẫu BCTC:
       - Mẫu 01: Bảng cân đối kế toán (Balance Sheet)
       - Mẫu 02: Kết quả hoạt động kinh doanh (P&L)
       - Mẫu 03: Lưu chuyển tiền tệ (Cash Flow — direct method)
       - Mẫu 04: Thuyết minh BCTC (Notes)
  → 4. Calculate ratios / disclosures per Circular 99
  → 5. Render PDF using reportlab / weasyprint
  → 6. Store PDF in bctc_consolidated.pdf_path
  → [User downloads / files with Tổng cục Thuế]
```

### BCTC Template Mapping

| Mẫu | Vietnamese Name | English | Source |
|---|---|---|---|
| 01 | Bảng cân đối kế toán | Balance Sheet | Circular 99/2025 |
| 02 | Kết quả hoạt động kinh doanh | Income Statement | Circular 99/2025 |
| 03 | Lưu chuyển tiền tệ | Cash Flow Statement | Circular 99/2025 |
| 04 | Thuyết minh BCTC | Notes to FS | Circular 99/2025 |
| 05 | Báo cáu tình hình tài chính (consolidated) | Group FS cover | Circular 99/2025 |
| 06 | Báo cáo lưu chuyển tiền tệ (indirect) | CF indirect method | Circular 99/2025 |

--- END OF FILE ---
