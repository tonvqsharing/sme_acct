# Fiscal Years & Accounting Periods Module — User Journeys

## UJ-1 Kế toán tổng hợp — monthly close (everyday loop)

Month-end. Open Tasks → shows "Tháng 02/2026 kết thúc 28/02; chưa khóa sổ".
System banner: period status on every posting screen.
Journey: verify posted vouchers → run month-end checks (revaluation, accrual,
bank recon) → request close with reason → wait for Kế toán trưởng approval →
see LOCKED badge → move to March. Every late posting attempt shows
"Kỳ kế toán tháng 02/2026 đã khóa sổ — 409" toast.
Feel: safe, no silent data corruption, clear blocking message.

## UJ-2 Kế toán trưởng — year-end close (annual)

Dec 31. Dashboard: "2026 — 12/12 kỳ đã khóa. Sẵn sàng khóa sổ năm."
Click "Khóa sổ năm": system previews preconditions (all locked, no drafts) →
"Chạy kết chuyển 911/421" → shows closing summary (doanh thu, chi phí,
lợi nhuận, TK 421 balance) → confirm → 2027 created with "Số đầu năm".
Review opening balances report; print BCTC năm.
Feel: guided, auditable, no manual journal guesswork.

## UJ-3 Kế toán trưởng — fiscal year change (one-off)

Group demands FY 01/07. Wizard:
1. Choose new period type (FISCAL_JUL) — system validates quarter alignment.
2. Shows transition period (short period) + BCTC snapshot preview.
3. Checklist "Thông báo cơ quan thuế" — download notice template, attach
   evidence ref.
4. Confirm → new FY live; opening balances carried as "Số đầu năm".
Feel: legal compliance front-and-center; evidence stored.

## UJ-4 Kiểm toán viên — audit trail

Receives access (AUDITOR). Opens FY 2026 → Periods → history.
Sees chain: each lock/unlock event with actor, timestamps, reason, checksum.
Click "Xác minh" → chain verified OK. Requests adjustment →
Kế toán trưởng reopens period with justification ref → entry posted →
re-locked. Exports evidence package.
Feel: transparent, tamper-evident, professional.

## UJ-5 Giám đốc / Chủ doanh nghiệp — oversight

Dashboard widget: current FY, period statuses, pending close approvals.
Receives notification when Kế toán trưởng requests period close.
Approves from mobile. Sees lock history summary in audit reports.
Feel: control without touching books.

## UJ-6 Admin — FISCAL_15 legacy cleanup (upgrade day)

After deploy: dashboard flags "Công ty X: kỳ kế toán không hợp lệ (FISCAL_15)".
Opens company → redefines FY per law (quarter-aligned) → system re-seeds
periods, blocks posting meanwhile. Old periods marked Legacy.
Feel: clear upgrade path, no silent illegal state.

## UJ-7 Quản trị viên — per-journal lock enhancement (later)

Accounting wants closing sales journal before purchases. Toggles JOURNAL
scope: lock journal + period combination. Posting to closed journal in open
period → blocked; other journals unaffected.
Feel: granular control (Tryton Journal Period parity).
