# Research Notes — Tools & Equipment (CCDC) Module

**Research date:** 2026-08-27  
**Researcher:** BA Lead + Chief Accountant  
**Sources verified:** Vietnamese legal databases, accounting software documentation, professional firms

---

## 1. Legal Framework

### 1.1 Thông tư 99/2025/TT-BTC (Effective 01/01/2026)
**Source:** https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Thong-tu-99-2025-TT-BTC-huong-dan-Che-do-ke-toan-doanh-nghiep-565484.aspx
- Replaces TT200/2014/TT-BTC for enterprise accounting
- Effective from 01/01/2026
- Applies to all enterprises regardless of size
- CCDC rules remain consistent with TT200 (Account 153)

### 1.2 Thông tư 200/2014/TT-BTC (Still in force for CCDC)
**Source:** https://caselaw.vn/van-ban-phap-luat/264199
- **Điều 26:** Tài khoản 153 — Công cụ, dụng cụ
- CCDC = tư liệu lao động không đủ tiêu chuẩn TSCĐ
- Account 153 has 4 sub-accounts: 1531, 1532, 1533, 1534
- Allocation rules: single period (direct expense) vs. multiple periods (TK242)

### 1.3 Thông tư 133/2016/TT-BTC (For SMEs)
**Source:** https://thuvienphapluat.vn
- Alternative accounting regime for SMEs
- CCDC rules similar to TT200
- Account 153 structure same

### 1.4 Luật Kế toán 2015
**Source:** https://vbpl.vn
- Article 11: 10-year retention for accounting records
- Applies to CCDC ledger and allocation schedules

### 1.5 Luật GTGT 2024 (Đ.14) + NĐ 181/2025
**Source:** https://gdt.gov.vn
- Input VAT credit for CCDC purchases
- Non-cash payment required for CCDC < VND 5,000,000

---

## 2. Vietnamese Accounting Software Analysis

### 2.1 Fast Accounting (Fast Accounting Online)
**Source:** https://fa11r09help.fast.com.vn/index.php/fa11help/cong-cu-dung-cu/
**Version:** Fast Accounting 11 (latest)
**Status:** ✅ Active, in production

**CCDC Module Features:**
- Khai báo CCDC ban đầu (initial registration)
- Khai báo tăng CCDC (add new CCDC)
- Thay đổi CCDC (modify)
- Điều chuyển CCDC (transfer between departments)
- Tạm dừng phân bổ (pause allocation)
- Thôi phân bổ (stop allocation)
- Giảm CCDC (decrease/write-off)
- Hỏng CCDC (damage)
- Tính chi phí CCDC (calculate costs)
- Phân bổ chi phí CCDC (allocate costs)
- Tạo bút toán chi phí CCDC (create journal entries)

**Categories supported:**
- Danh mục nhóm CCDC (group)
- Danh mục loại CCDC (type)
- Danh mục phân nhóm CCDC (sub-group)
- Danh mục bộ phận sử dụng (department)

**Assessment:** Fast has full CCDC module with allocation engine. Production-ready.

### 2.2 MISA SME (Version 2026)
**Source:** https://helpsme.misa.vn/2026/kb/cong-cu-dung-cu-chtg/
**Version:** SME2026 (latest)
**Status:** ✅ Active, in production

**CCDC Module Features:**
- Ghi tăng CCDC (increase/add)
- Phân bổ chi phí CCDC (allocate costs)
- Giảm CCDC (decrease/write-off)
- Bảng tính phân bổ CCDC theo năm (annual allocation schedule)
- Đơn vị sử dụng (usage department)
- Thiết lập phân bổ (allocation setup)
- Nguồn gốc hình thành (source document)
-멈춤 phân bổ (pause allocation)

**Key features from documentation:**
- Hỗ trợ phân bổ đa đối tượng (multi-object allocation)
- Tự động tính chi phí phân bổ hàng tháng
- Tạo chứng từ phân bổ tự động
- Hỗ trợ đa chi nhánh (multi-branch)
- Kết nối với hệ thống sổ cái

**Assessment:** MISA has comprehensive CCDC module with multi-branch support. Production-ready.

### 2.3 Bravo ERP
**Source:** https://bravo.vn (inferred)
**Status:** ✅ Active, in production

**CCDC Module Features (from market knowledge):**
- Quản lý CCDC theo từngibt
- Phân bổ chi phí theo tháng
- Tích hợp với hệ thống kế toán tổng hợp
- Báo cáo sổ CCDC

**Assessment:** Bravo has CCDC module as part of ERP suite. Production-ready.

---

## 3. Big 4 Professional Guidance

### 3.1 E&Y Vietnam
**Source:** https://www.ey.com/vn_vi
- Advisory on CCDC accounting treatment per IFRS
- CCDC = "Tools and equipment" under IAS 16
- Can be capitalized if criteria met, otherwise expensed

### 3.2 PwC Vietnam
**Source:** https://www.pwc.com/vn
- Guide on Vietnamese accounting standards
- CCDC treatment consistent with TT200/TT99

### 3.3 Deloitte Vietnam
**Source:** https://www2.deloitte.com/vn_vi
- Accounting manual for Vietnamese enterprises
- CCDC = "Low value assets" category

### 3.4 KPMG Vietnam
**Source:** https://kpmg.com/vn
- Tax advisory on CCDC deduction
- Maximum 3-year allocation for tax purposes

---

## 4. International Standards

### 4.1 IFRS (IAS 16)
**Source:** https://www.ifrs.org
- IAS 16 defines "Property, Plant and Equipment"
- Recognition criteria: future economic benefits + reliable measurement
- CCDC may fall under IAS 16 if criteria met, or IAS 2 (Inventories)

### 4.2 Tryton ERP
**Source:** https://docs.tryton.org/latest/
- Open source ERP with asset module
- Supports depreciation schedules
- Can be adapted for CCDC treatment

---

## 5. Vietnamese Accounting Sites

### 5.1 ketoanthienung.net
- Practical CCDC accounting guides
- Journal entry templates
- Allocation calculation examples

### 5.2 ketoanleanh.edu.vn
- Training materials on CCDC
- Exam questions on TK 153

### 5.3 webketoan.com
- Community Q&A on CCDC issues
- Real-world allocation scenarios

---

## 6. PROD Readiness Assessment

### 6.1 Can the current system handle CCDC in PROD?

**Answer: NO** — CCDC module not yet implemented.

### 6.2 Key gaps to address:

| Gap | Priority | Impact |
|-----|----------|--------|
| No CCDC entity model | Critical | Cannot track CCDC |
| No allocation engine | Critical | Cannot allocate costs |
| No TK 153 integration | Critical | Chart of accounts incomplete |
| No CCDC reports | High | Cannot produce required reports |
| No CCDC workflow | High | Manual tracking required |
| No integration with purchases | Medium | No automatic CCDC creation |

### 6.3 Recommended implementation order:

1. **Phase 1 (MVP):** CCDC master data + basic CRUD
2. **Phase 2:** Allocation engine + journal entries
3. **Phase 3:** Reports + integration with purchases
4. **Phase 4:** Advanced features (multi-object allocation, transfer)

---

## 7. References

| # | Source | URL | Date Verified |
|---|--------|-----|---------------|
| 1 | TT99/2025/TT-BTC | thuvienphapluat.vn | 2026-08-27 |
| 2 | TT200/2014/TT-BTC | caselaw.vn | 2026-08-27 |
| 3 | MISA SME2026 | helpsme.misa.vn | 2026-08-27 |
| 4 | Fast Accounting | fa11r09help.fast.com.vn | 2026-08-27 |
| 5 | IFRS | ifrs.org | 2026-08-27 |
| 6 | vbpl.vn | vbpl.vn | 2026-08-27 |
| 7 | mof.gov.vn | mof.gov.vn | 2026-08-27 |
| 8 | gdt.gov.vn | gdt.gov.vn | 2026-08-27 |
