# RBAC Use Cases — Vietnamese SME Accounting System

## Legend
- **HP**: Happy Path (success scenario)
- **AP**: Alternative Path (valid but different outcome)
- **EP**: Exception Path (error, denial, edge case)
- **CODE**: RBAC decision outcome (ALLOW/DENY)
- **HTTP**: Status code returned

---

## U-01: Create Invoice

### HP-01: ACCOUNTANT Creates Invoice (Successful)
| Step | Actor | Action | RBAC Check | Result |
|---|---|---|---|---|
| 1 | ACCOUNTANT | Logs in | `enforce("ACCOUNTANT", "/api/v1/invoices", "post")` | ALLOWED (session: user.role=ACCOUNTANT) |
| 2 | ACCOUNTANT | Calls `POST /api/v1/invoices` | Enforcer checks subject+resource+action | ALLOWED |
| 3 | Flask route | Validates input, constructs Invoice domain entity | TaxId/AccountCode VOs validate regex | Domain validation passes |
| 4 | Repository | Persists InvoiceModel + items to DB | MST uniqueness check via UNIQUE constraint | Persisted |
| 5 | AuditLogService | Creates audit record | `entity_type="INVOICE"`, `action="CREATE"`, `actor_id=user.id` | Recorded |
| 6 | Response | `201 Created` + invoice details | — | UI shows success message |

**Data Flow**: ACCOUNTANT → Flask route → Casbin enforcer → InvoiceService → SQLAlchemyRepository → SQLite → audit_log

### AP-01: CHIEF_ACCOUNTANT Creates Invoice (Also Allowed)
| Step | Actor | RBAC Difference | Outcome |
|---|---|---|---|
| 1 | CHIEF_ACCOUNTANT | Same endpoint, different role | `enforce("CHIEF_ACCOUNTANT", "/api/v1/invoices", "post")` → **ALLOWED** |
| 2 | — | Chief can create invoices too (not just ACCOUNTANT) | UI may show additional fields or validation rules |

### EP-01: ACCOUNTANT Attempts to Create Invoice for Different Company
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/invoices/{company_id}", "post")` | **DENIED** — company not in ACCOUNTANT's scoped company_id list |
| 2 | Flask route | Returns `403 Forbidden` | `{"error": "RBAC denied: ACCOUNTANT cannot access company XXXX", "code": "RBAC_DENIED_COMPANY"}` |
| 3 | UI | Shows error banner | "Bạn không có công ty này để lập chứng từ." |
| 4 | AuditLog | `entity_type="RBAC"`, `action="DENY"`, `after_value="company_id=XXXXX by ACCOUNTANT"` | Immutable record |

**RBAC Mechanism**: Policy CSV has company-scoped rules or service-layer checks `company_id IN user.managed_company_ids`

### EP-02: ACCOUNTANT Attempts to Post (Publish) Invoice Without Approval
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | Calls `POST /api/v1/invoices/{id}/post` | `enforce("ACCOUNTANT", "/api/v1/invoices/{id}/post", "post")` → **DENIED** |
| 2 | — | SoD rule S-01: ACCOUNTANT cannot approve own entries |  |
| 3 | Flask route | `403 Forbidden` | `{"error": "RBAC denied: ACCOUNTANT cannot post invoice without CHIEF_ACCOUNTANT approval", "code": "RBAC_SOD_INVOICE_POST"}` |
| 4 | UI | Error message + "Submit for Approval" CTA |  |
| 5 | AuditLog | `action="RBAC_DENY_SOD"` |  |

### HP-02: CHIEF_ACCOUNTANT Posts/Approves Invoice
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | CHIEF_ACCOUNTANT | Calls `POST /api/v1/invoices/{id}/post` | `enforce("CHIEF_ACCOUNTANT", "/api/v1/invoices/{id}/post", "post")` → **ALLOWED** |
| 2 | — | SoD satisfied: CREATOR (ACCOUNTANT) ≠ POSTER (CHIEF_ACCOUNTANT) |  |
| 3 | InvoiceService | Calls `invoice.post()` — validates balance (tol 0.01), status must be DRAFT | Business logic validations pass |
| 4 | Repository | Updates InvoiceModel.status = APPROVED, vat_total, grand_total | DB committed |
| 5 | AuditLog | `action="POST"`, `after_value=invoice.json()` |  |
| 5 | Response | `200 OK` + approved invoice JSON | UI shows "Đã duyệt" badge |

---

## U-02: Create Voucher

### HP-01: ACCOUNTANT Creates Voucher (Self-Post Within Tolerance)
| Step | Actor | RBAC Check | Business Logic |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/vouchers", "post")` → **ALLOWED** |  |
| 2 | Flask route | Validates voucher: `Voucher.post()` debit/credit balance (tol 0.01) | Balance within 0.01 → OK |
| 3 | Voucher.post() | Recalculates subtotal, vat_total, grand_total via `Invoice.add_item()` pattern | Recalculation passes |
| 4 | Repository | Persists VoucherModel + VoucherLineModel(s) |  |
| 5 | AuditLog | `action="CREATE"` |  |
| 5 | Response | `201 Created` |  |

### EP-01: ACCOUNTANT Creates Voucher With Imbalanced Debit/Credit ( > 0.01 tolerance)
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/vouchers", "post")` → **ALLOWED** (creation allowed) |  |
| 2 | Flask route | `Voucher.post()` called with unbalanced entries | `debit = 1,000,000`, `credit = 990,000` → difference 10,000 > 0.01 |
| 3 | Domain exception | `InvalidVoucher: Chứng từ không cân bằng` raised |  |
| 4 | Flask route | `422 Unprocessable Entity` | `{"error": "Chứng từ không cân bằng nợ/có", "code": "VOUCHER_UNBALANCED"}` |
| 4 | AuditLog | `action="VOUCHER_UNBALANCED"` |  |
| 4 | UI | Error list: "Nợ: 1.000.000, Có: 990.000, lệch: 10.000 vượt quá tolerance 0.01" |  |

### EP-02: ACCOUNTANT Attempts to Post Voucher From Non-DRAFT Status
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/vouchers/{id}/post", "post")` → **DENIED** | SoD + status check |
| 2 | — | Voucher must be in DRAFT status to post |  |
| 3 | Flask route | `403 Forbidden` | `{"error": "Voucher không ở trạng thái DRAFT", "code": "VOUCHER_NOT_DRAFT"}` |
| 4 | AuditLog | `action="POST_DENIED_NOT_DRAFT"` |  |

### HP-02: CHIEF_ACCOUNTANT Approves/Posts Another's Voucher
| Step | Actor | RBAC Check | Outcome |
|---|---|---|---|
| 1 | CHIEF_ACCOUNTANT | `enforce("CHIEF_ACCOUNTANT", "/api/v1/vouchers/{id}/post", "post")` → **ALLOWED** |  |
| 2 | — | Chief can post vouchers created by ACCOUNTANT | SoD satisfied |
| 3 | Voucher.post() | Business validations (balance, status) | Pass/fail based on data |
| 4 | Repository + AuditLog | Same as HP-01 |  |

---

## U-03: System Configuration Changes

### HP-01: ADMIN Edits CONFIG-Type Flag (With Audit Log + 2nd Approval Pattern)
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/system-config/vat-rates", "patch")` → **ALLOWED** |  |
| 2 | Flask route | `SystemSettingsService.update_config()` called |  |
| 3 | Service | Sets `config.vat_rates` = new frozenset; `config.config_version += 1` | Version increment for optimistic locking |
| 4 | Service | `config.updated_by = actor.id`; repo.update(config) |  |
| 5 | Repository | `UPDATE company_config SET ... WHERE company_id = ?` | DB commit with version WHERE clause |
| 6 | AuditLogService | `create(entity_type="CONFIG", action="UPDATE", after_value=new_value, before_value=old_value, actor_id=actor.id)` | Immutable record |
| 6 | Response | `200 OK` + new config version | UI shows "Cập nhật thành công, phiên bản CXX" |

### AP-01: ADMIN Edits CONFIG-Type Flag (Single-User — Not Recommended)
| Step | Actor | RBAC Check | Outcome |
|---|---|---|---|
| 1 | ADMIN | Same as HP-01 → **ALLOWED** |  |
| 2 | — | No 2nd approval enforced at RBAC level (v1) | — |
| 3 | — | **Risk**: Single point of change without audit trail for compliance | — |
| 4 | — | **Mitigation**: Full SoD enforcement comes in later phases (BRD §4.1 S-03) |  |

### EP-01: ACCOUNTANT Attempts to Edit CONFIG-Type System Flag
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/system-config/vat-rates", "patch")` → **DENIED** |  |
| 2 | Flask route | `403 Forbidden` | `{"error": "RBAC denied: ACCOUNTANT cannot edit system config", "code": "RBAC_DENY_CONFIG_EDIT"}` |
| 3 | UI | Error banner + "Only ADMIN can modify system settings" |  |
| 3 | AuditLog | `action="RBAC_DENY_CONFIG_EDIT"` |  |

### EP-02: ACCOUNTANT Attempts to Edit LAW-Type Flag (Without Migration)
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/system-config/legal-rep", "patch")` → **DENIED** |  |
| 2 | — | LAW-type flags immutable without migration per BRD §2 legal foundations |  |
| 3 | Domain exception | `FlagLockedError: Cờ hệ thống loại LAW không thể thay đổi mà không có migration patch` |  |
| 4 | Flask route | `403 Forbidden` | `{"error": "Cờ LAW không thể thay đổi không có migration", "code": "LAW_IMMUTABLE_NO_MIGRATION"}` |
| 4 | AuditLog | `action="LAW_IMMUTABLE_ATTEMPT"` |  |
| 4 | UI | "Các cờ hệ thống loại LAW (law type) là hằng pháp lý, chỉ có thể thay đổi qua patch migration." |  |

### HP-03: ADMIN Edits LAW-Type Flag With Migration
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/system-config/legal-rep", "patch with migration")` → **ALLOWED** |  |
| 2 | — | Requires `X-Migration-Version: <ver>` header + audit log entry |  |
| 3 | Service | Validates migration version against approved list |  |
| 4 | Service | Applies change; `config.legal_reviewed_by = ADMIN.id`; `config.legal_reviewed_at = today()` |  |
| 5 | AuditLog | `action="LAW_MIGRATION"`, `after_value=new`, `before_value=old`, `legal_basis="Nghị định XX/2023"` |  |
| 6 | Response | `200 OK` + migration confirmation |  |

---

## U-04: Period Lock / Unlock

### HP-01: CHIEF_ACCOUNTANT Locks Accounting Period
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | CHIEF_ACCOUNTANT | `enforce("CHIEF_ACCOUNTANT", "/api/v1/period-locks", "lock")` → **ALLOWED** |  |
| 2 | Flask route | `SystemSettingsService.lock_period()` called |  |
| 3 | Service | Checks `period_locks` table: if already locked → error; otherwise inserts new lock row |  |
| 4 | Service | `config.updated_by = actor.id`; `config.config_version += 1` |  |
| 5 | Repository | `INSERT INTO period_locks (company_id, period_start, period_end, is_locked, locked_at, locked_by_id)` | DB commit |
| 6 | InvoiceService/VoucherService (called later) | `validate_active_for_transaction()` checks `period_locks.is_locked = TRUE` → blocks new entries |  |
| 6 | AuditLog | `action="PERIOD_LOCK"` |  |
| 6 | Response | `200 OK` + locked period details | UI shows " Kỳ đã khóa" |

### AP-01: ADMIN Locks Period (Also Allowed)
| Step | Actor | RBAC Check | Outcome |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/period-locks", "lock")` → **ALLOWED** | Same process, different role |
| 2 | — | ADMIN has broader privileges |  |

### EP-01: ACCOUNTANT Attempts to Lock Period
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/period-locks", "lock")` → **DENIED** |  |
| 2 | Flask route | `403 Forbidden` | `{"error": "RBAC denied: only CHIEF_ACCOUNTANT/ADMIN can lock periods", "code": "RBAC_DENY_PERIOD_LOCK"}` |
| 3 | UI | Error message | "Chỉ Trưởng Khoản/Kế Toán chủ hệ thống mới khóa kỳ." |
| 3 | AuditLog | `action="RBAC_DENY_PERIOD_LOCK_ACCOUNTANT"` |  |

### EP-02: ADMIN Attempts to Lock Already-Locked Period
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/period-locks/{id}/lock", "lock")` → **DENIED** (idempotency) |  |
| 2 | Flask route | Service checks `period_locks.exists(company_id, period_start, period_end)` and `is_locked = TRUE` |  |
| 3 | Response | `409 Conflict` | `{"error": "Kỳ kế toán đã khóa", "code": "PERIOD_ALREADY_LOCKED"}` |
| 3 | AuditLog | `action="PERIOD_LOCK_REJECT_DUPLICATE"` |  |
| 3 | UI | Warning: "Kỳ này đã khóa, không thể khóa lại." |  |

### HP-02: ADMIN Unlocks Period
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/period-locks/{id}/unlock", "unlock")` → **ALLOWED** |  |
| 2 | Flask route | `SystemSettingsService.unlock_period()` called |  |
| 3 | Service | `DELETE FROM period_locks WHERE company_id = ? AND period_start = ? AND period_end = ?` | Physical delete (or soft-set is_locked=FALSE) |
| 4 | Service | `config.config_version += 1`; `repo.update(config)` |  |
| 5 | AuditLog | `action="PERIOD_UNLOCK"` |  |
| 6 | Response | `200 OK` + unlocked period | UI shows " Kỳ đã mở khóa" |

---

## U-05: Audit Log Access

### HP-01: AUDITOR Reads Audit Log (Read-Only)
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | AUDITOR | `enforce("AUDITOR", "/api/v1/audit-log", "read")` → **ALLOWED** |  |
| 2 | Flask route | `AuditLogService.get_by_entity()` called with `entity_type="RBAC"` or filters |  |
| 3 | Repository | `SELECT FROM audit_log WHERE ...` (no DELETE possible — DB role REVOKE DELETE) |  |
| 4 | Response | `200 OK` + paginated list of audit records | UI shows filter controls |
| 4 | Data | Each record: `id, entity_type, action, before_value, after_value, actor_id, changed_at, checksum` |  |

### EP-01: ACCOUNTANT Attempts to Read Audit Log (Also Allowed but Limited)
| Step | Actor | RBAC Check | Outcome |
|---|---|---|---|
| 1 | ACCOUNTANT | `enforce("ACCOUNTANT", "/api/v1/audit-log", "read")` → **ALLOWED** | All roles can read audit log per policy |
| 2 | — | But cannot destroy/delete or modify any records |  |
| 3 | UI | Read-only view; no edit buttons, no destroy actions |  |
| 3 | AuditLog | `action="ACCOUNTANT_READ_AUDIT"` recorded |  |

### EP-02: AUDITOR Attempts to Destroy Audit Record (Before 10-Year Retention)
| Step | Actor | RBAC Check | Result |
|---|---|---|---|
| 1 | AUDITOR | `enforce("AUDITOR", "/api/v1/audit-log/{id}/destroy", "delete")` → **DENIED** | No write/delete policies for AUDITOR in policy CSV |
| 2 | Flask route | `403 Forbidden` | `{"error": "RBAC denied: AUDITOR cannot destroy audit records", "code": "RBAC_DENY_AUDIT_DESTROY"}` |
| 3 | — | Must wait minimum 10 years per Luật Kế toán 2015 Art. 30 |  |
| 2 | UI | "Chỉ có thể hủy (soft-delete) sau 10 năm tuân theo Luật Kế toán 2015." |  |
| 3 | AuditLog | `action="RBAC_DENY_AUDIT_DESTROY_EARLY"` |  |

### EP-03: ADMIN Destroys Audit Record After 10-Year Retention (With Audit)
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | ADMIN | `enforce("ADMIN", "/api/v1/audit-log/{id}/destroy", "delete")` → **ALLOWED** |  |
| 2 | — | Only after verifying `changed_at <= today - 10 years` |  |
| 3 | Service | Calls `AuditLogService.verify_destruction_eligibility(record_id, changed_at)` |  |
| 4 | Eligible? | If YES: marks `destroyed_at = now()` in DB (soft delete; record preserved with checksum) |  |
| 5 | If NO: Returns `409 Conflict` + years remaining |  |
| 6 | AuditLog | `action="DESTROY_AUDIT_AFTER_10Y"` + `after_value={"years_elapsed": N, "reason": "compliant"}` |  |
| 6 | Response | `200 OK` + destruction confirmation |  |

---

## U-06: Role Hierarchy & Promotion

### HP-01: CHIEF_ACCOUNTANT Promoted to ADMIN
| Step | Actor | RBAC Check | Process |
|---|---|---|---|
| 1 | CHIEF_ACCOUNTANT | Current role: `CHIEF_ACCOUNTANT` |  |
| 2 | Admin action | Updates `auth_user_roles` table: `user_id = ?`, `role = 'ADMIN'` |  |
| 3 | Policy reload | `/api/v1/rbac/reload` triggered → enforcer reloads `rbac_policy.csv` |  |
| 4 | Enforcer | Now has `g, CHIEF_ACCOUNTANT, ADMIN` in role_definition |  |
| 5 | Previous actions | `enforce("CHIEF_ACCOUNTANT", "...", "...")` still ALLOWED (legacy) |  |
| 6 | New actions | `enforce("ADMIN", "...", "...")` now ALLOWED (expanded permissions) |  |
| 7 | AuditLog | `action="ROLE_PROMOTION"`, `after_value="CHIEF_ACCOUNTANT→ADMIN"`, `actor_id=promoter_id` |  |
| 8 | Response | `200 OK` + new role assignment confirmed |  |

### AP-01: Self-Service Role Promotion (Not Recommended)
| Step | Actor | RBAC Check | Outcome |
|---|---|---|---|
| 1 | User | Attempts `POST /api/v1/rbac/promote-self?to=ADMIN` | `enforce(current_user.role, "...", "→ADMIN")` → **DENIED** |
| 2 | Flask route | `403 Forbidden` | "Bạn không được phép thay đổi role của chính mình." |
| 2 | AuditLog | `action="RBAC_SELF_PROMOTE_DENIED"` |  |

---

## Summary Table: All Use Cases

| Use Case | Role | Action | RBAC Outcome | HTTP | Key Business Rule |
|---|---|---|---|---|---|
| U-01-HP | ACCOUNTANT | Create invoice | ALLOWED | 201 | MST/AccountCode VO validation |
| U-01-EP | ACCOUNTANT | Create invoice for other company | DENIED | 403 | Company scoping |
| U-02-HP | ACCOUNTANT | Create voucher (balanced) | ALLOWED | 201 | Tolerance 0.01 |
| U-02-EP | ACCOUNTANT | Create voucher (unbalanced >0.01) | DENIED | 422 | Voucher balance rule |
| U-03-HP | ADMIN | Edit CONFIG flag | ALLOWED | 200 | config_version increment |
| U-03-EP | ACCOUNTANT | Edit CONFIG flag | DENIED | 403 | Role-based |
| U-03-EP2 | ACCOUNTANT | Edit LAW flag | DENIED | 403 | Law immutable without migration |
| U-04-HP | CHIEF_ACCOUNTANT | Lock period | ALLOWED | 200 | Period lock enforcement |
| U-04-EP | ACCOUNTANT | Lock period | DENIED | 403 | Role requirement |
| U-05-HP | AUDITOR | Read audit log | ALLOWED | 200 | Read-only for all |
| U-05-EP | AUDITOR | Destroy audit record (early) | DENIED | 403 | 10-yr retention |
| U-06-HP | CHIEF_ACCOUNTANT → ADMIN | Role promotion | ALLOWED with reload | 200 | Hierarchy: g, CHA, ADMIN |

All 65 existing unit/integration tests should continue passing since pycasbin has **no existing code** in the codebase to break — this is a new implementation layer.