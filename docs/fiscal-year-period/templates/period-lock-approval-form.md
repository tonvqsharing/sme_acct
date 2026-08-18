# Period Lock Approval Form
(Đơn đề nghị khóa sổ / mở khóa kỳ kế toán)

| Field | Value |
|---|---|
| Công ty / MST | {company_name} / {tax_id} |
| Kỳ kế toán | {period_label} ({start_date} → {end_date}) |
| Hành động | ☐ Khóa sổ (CLOSE) · ☐ Mở khóa (REOPEN) |
| Lý do (bắt buộc) | {reason} |
| Số chứng từ liên quan | {ref_documents} |
| Người đề nghị | {requester} ({role}) |
| Người phê duyệt | {approver} ({role}) — KHÔNG được trùng người đề nghị (SOD) |
| Approval ref | {approval_ref} |

## SOD check
- [ ] approver ≠ requester (else system rejects: SelfApprovalError)

## Approver decision
- [ ] ĐỒNG Ý
- [ ] TỪ CHỐI

| Approver | Date/Time | Signature |
|---|---|---|
| | | |

---
*Kết quả ghi nhận hệ thống: event_id = {event_id}, checksum = {checksum},
trạng thái kỳ: OPEN / LOCKED / YEAR_CLOSED.*
