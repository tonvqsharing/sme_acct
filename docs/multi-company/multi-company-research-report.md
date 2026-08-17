# Multi-Company / Master-Module Research Report

## Executive Summary

1. **Fast Business Online** (ERP line) explicitly supports multi-company with dedicated "Fast Consolidated Reports" module for BCTC hợp nhất; **Fast Accounting** (desktop, SMEs) is single-company only — source: fast.com.vn product pages.
2. **MISA AMIS** platform does not advertise explicit multi-tenant or master-company accounting in public product pages; MISA ASP is a service-provision marketplace, not enterprise multi-company software — source: amis.misa.vn, asp.misa.vn.
3. **BravoERP** (bravoerp.com) — website returned no readable content ("Bravo erp" only); multi-company capability **cannot be verified** from public sources.
4. **Tryton** has a first-class `company` module (since v1.0, 2008; current v8.0, Apr 2026) that is part of the core server — multi-company is native, production-ready, but **no Vietnamese localization visible** in official docs.
5. **Vietnamese legal framework** requires per-company tax ID, chart-of-accounts, and tax filing per legal entity; consolidated BCTC is required only for parent companies under Enterprise Law 2020. No explicit "multi-company software" regulatory mandate found from primary sources in this research session (gdt.gov.vn and vbpl.vn both blocked/errored).
6. **VAA** runs training on group accounting, IFRS for SMEs, and "Kế toán trưởng Tổng công ty/Tập đoàn" — signals professional demand for multi-company skills, but no formal standard issued.
7. **IFRS 10/IFRS 3** govern consolidated financial statements globally; Vietnam's Ministry of Finance has an IFRS adoption roadmap. IFRS for SMEs has an active Exposure Draft on Consolidation Exception (comments due Sep 2026) — source: ifrs.org.
8. **Big4 Vietnam** (EY, KPMG) publish "Doing Business in Vietnam" and IFRS guidance; no specific product guidance or whitepapers on master-company/consolidation for Vietnamese accounting software were found on their public Vietnam sites in this session. PwC/Deloitte URLs not reachable.

---

## Product Survey

### Fast

- **Multi-company support:** YES — Fast Business Online (ERP, cloud) only. NOT in Fast Accounting (desktop, SME).
- **Master-company features:**
  - Dedicated module "Báo cáo tài chính Hợp nhất – Fast Consolidated Reports"
  - Receives data from subsidiaries; tracks list of companies not yet submitted
  - Calculates consolidated figures; supports adjusting entries pre/post consolidation
  - Presents: BCTC tình hình tài chính hợp nhất, KQKD hợp nhất, LCTTiền tệ hợp nhất (direct & indirect method), thuyết minh BCTC
  - Supports "Nhóm hợp nhất" (consolidation group) configuration
  - IFRS compliance mentioned for Fast Business Online (separate product page)
- **Production readiness:** YES — deployed for enterprise groups (Sun Group, Vinpearl, Cảng Đà Nẵng, PVOIL, FLC, TCT Hàng hải Việt Nam, J&T Express 30 units, etc.)
- **Source:** https://fast.com.vn/phan-mem-erp-fast-business-online-bao-cao-tai-chinh-hop-nhat-fast-consolidated-reports/ ; https://fast.com.vn/phan-mem-erp-fast-business-online/

### MISA

- **Multi-company support:** NOT CONFIRMED from public product pages. AMIS Kế toán (amis.misa.vn/amis-ke-toan/) is designed for single enterprise; MISA ASP is a service marketplace connecting businesses with accounting firms — not multi-entity accounting software.
- **Master-company features:** None explicitly stated in public pages reviewed. AMIS Platform advertises "Data360" (unified data) and general "hợp nhất báo cáo thông minh" for public-sector (iHOS), but no confirmed multi-company accounting module found.
- **Production readiness:** UNKNOWN for multi-company. AMIS is production-ready for single-company enterprise (300,000+ enterprise users claimed).
- **Source:** https://amis.misa.vn/amis-ke-toan/ ; https://asp.misa.vn/ ; https://www.misa.vn/

### BravoERP

- **Multi-company support:** UNKNOWN
- **Master-company features:** UNKNOWN
- **Production readiness:** UNKNOWN — bravoerp.com and www.bravoerp.com both returned only the phrase "Bravo erp" with no further content. Product cannot be assessed from public sources.
- **Source:** https://bravoerp.com (no readable content retrieved)

### Tryton

- **Multi-company support:** YES — native to core `company` module since v1.0 (2008). Current stable: v8.0 (released 2026-04-20).
- **Master-company features:**
  - `company.company` model: each company is a Party; users can be linked to multiple companies
  - User selects "current company" — all data access filtered accordingly
  - Models link records to company; accesscontrol is company-aware
  - `company.employee` with org hierarchy (supervisor chains)
  - Multi-currency, multi-branch accounting supported via company records
  - Separate COA per company is standard (Tryton's `account` module is company-scoped)
  - No explicit "master-company consolidation" module found in core; requires custom or third-party consolidation module
  - **No Vietnamese translation/locale visible** in official docs
- **Production readiness:** YES — mature (18 years of releases); used globally. Vietnamese compliance (Mẫu số, Tỷ giá, BCTC formats per Thông tư 99/2025/TT-BTC) requires customization.
- **Source:** https://docs.tryton.org/latest/modules-company/ ; https://docs.tryton.org/latest/modules-company/design.html ; https://docs.tryton.org/latest/modules-company/releases.html

---

## Legal & Regulatory Requirements (Vietnam)

### Taxation

- **Primary law:** Luật Quản lý thuế 2019 (Law on Tax Management); Circular 99/2025/TT-BTC (accounting regime, effective 2026); Circular 58/2026/TT-BTC (micro-enterprises, effective 01/07/2026)
- **Per-company requirements (mandatory):**
  - Each legal entity has its own **Mã số thuế** (tax ID) — must be registered separately
  - Separate **kê khai thuế GTGT, Thuế TNDN, Thuế TNCN** per legal entity
  - Separate accounting books per legal entity required under Luật Kế toán 2015 (Law on Accounting)
  - Each legal entity files **BCTC** independently
- **Consolidated reporting:** Required only for parent companies of corporate groups (>=2 subsidiaries under control) per Luật Doanh nghiệp 2020 (Enterprise Law) and Circular 200/2014/TT-BTC (old) / Circular 99/2025 (new regime). Parent company must prepare **BCTC hợp nhất** when it controls ≥1 subsidiary.
- **Note:** gdt.gov.vn returned transport error and vbpl.vn returned 403 during this session — these conclusions are based on published legal framework knowledge, NOT confirmed from live primary source fetch in this session.

### Customs / Insurance / BHXH

- **Customs:** customs.gov.vn (Tổng cục Hải quan) accessible — no multi-company accounting content found on homepage. Each legal entity declares customs independently under its own E-invoice and Mã số thuế.
- **BHXH:** baohiemxahoi.gov.vn accessible — no multi-entity or master-company content found. BHXH declarations are per legal entity (per mã số BHXH đơn vị). From August 2026: reorganized from 35 regional BHXH offices to 34 provincial offices.
- **Sources:** https://customs.gov.vn ; https://baohiemxahoi.gov.vn

### dịch vụ công (Gov Services)

- dichvucong.gov.vn accessible — National Public Service Portal, hosted by Ministry of Public Security data center. No multi-company accounting module requirements found at homepage level.
- **Source:** https://dichvucong.gov.vn

---

## Accounting Standards

### VAA (Vietnam Federation of Accountants & Auditors — vaa.net.vn)

- No formal multi-company accounting standard issued by VAA found.
- VAA's **Câu lạc bộ Kế toán trưởng toàn quốc (VCCA)** runs a training program specifically titled: "VAA ĐÀO TẠO QUẢN TRỊ CHIẾN LƯỢC, KẾ TOÁN – THUẾ CHO TỔNG CÔNG TY, TẬP ĐOÀN" — signals recognized professional demand for group accounting skills.
- VAA has run **IFRS training courses** (Khóa đào tạo Chuẩn mực Báo cáo tài chính quốc tế — Khoá 4 as of Aug 2026).
- Published article: *"Sửa đổi Luật kế toán: Những việc cấp bách và lâu dài"* (Jun 2026) — discussing Law on Accounting revision priorities.
- **Source:** https://vaa.net.vn/

### IFRS (ifrs.org)

- **IFRS 10** — Consolidated Financial Statements: defines control model for requiring consolidation
- **IFRS 3** — Business Combinations: acquisition method for initial consolidation
- **IFRS for SMEs** — currently under review for Consolidation Exception (Exposure Draft, comments due 09 Sep 2026)
- Vietnam's Ministry of Finance has an IFRS adoption roadmap for listed companies and large enterprises; domestic private companies use Vietnamese Accounting Standards (VAS) per Circular 99/2025/TT-BTC.
- **Source:** https://www.ifrs.org/ (standards pages confirmed; active projects on consolidation exception)

---

## Big4 Guidance

- **EY Vietnam** (ey.com/en_vn): Publishes *"Doing Business in Vietnam"* annually. Offers IFRS advisory and financial accounting advisory services for Vietnam. No specific whitepaper on master-company/consolidation for Vietnamese accounting software was found on ey.com/en_vn in this session. EY Vietnam does have a dedicated IFRS service page and financial accounting advisory team.
- **KPMG Vietnam** (kpmg.com/vn): Monthly "Policy Watch" newsletter covers regulatory changes. Offers chart of accounts and consolidation advisory as part of audit/financial services. No specific product guidance on master-company features in Vietnamese software found on homepage.
- **PwC Vietnam** (pwc.com.vn): URL not reachable in this session (malformed URL attempted; no content retrieved).
- **Deloitte Vietnam** (deloitte.com.vn): URL not reachable in this session.
- **Risk:** Software vendors may cite Big4 compliance in marketing without publicly documented standards alignment.

---

## Open Standards (IFRS)

| Standard | Scope | Relevance to Multi-Company |
|---|---|---|
| IFRS 10 | Consolidated Financial Statements | Mandatory when parent controls subsidiary; defines control, uniform accounting policies, elimination of intra-group |
| IFRS 3 | Business Combinations | Acquisition-date fair value; goodwill calculation |
| IAS 27 | Separate Financial Statements | Accounting for subsidiaries in separate (standalone) books |
| IFRS for SMEs (S107-S108) | SME consolidation exception | Allows exemption for subsidiary if parent produces consolidated FS; Exposure Draft open Sep 2026 |

Vietnam has **not fully adopted IFRS** — listed companies and large enterprises may opt in under MoF roadmap; most Vietnamese companies follow **VAS** (Chuẩn mực Kế toán Việt Nam) per Circular 99/2025/TT-BTC.

---

## Compliance Checklist (Mandatory Requirements for Vietnamese Accounting Software)

| # | Requirement | Legal Basis | Per-Company? | Consolidated? |
|---|---|---|---|---|
| 1 | Separate Mã số thuế per legal entity | Luật Quản lý thuế 2019 | ✅ Required | N/A |
| 2 | Separate Hệ thống tài khoản kế toán per legal entity | Luật Kế toán 2015; Thông tư 99/2025/TT-BTC | ✅ Required | Separate COA |
| 3 | Separate Sổ sách kế toán per legal entity | Luật Kế toán 2015 Art. 28 | ✅ Required | Harmonized policies |
| 4 | Separate Kê khai thuế GTGT/TNDN/TNCN | Luật Quản lý thuế 2019 | ✅ Required | N/A |
| 5 | Separate Hóa đơn điện tử per legal entity | Nghị định 123/2024/NĐ-CP; Tổng cục Thuế recognition | ✅ Required | N/A |
| 6 | Separate BHXH/BHYT declarations per legal entity | Luật BHXH 2024; NĐ 158/2025/NĐ-CP | ✅ Required | N/A |
| 7 | BCTC hợp nhất (Consolidated B/S, P&L, CF) | Luật Doanh nghiệp 2020 Art. 218-224 | ❌ Only parent | ✅ Required for parent with subsidiaries |
| 8 | Thuyết minh BCTC hợp nhất | Circular 200/2014 (old) / Circular 99/2025 (new) | N/A | ✅ Required |
| 9 | Bút toán điều chỉnh hợp nhất (NST/NLD eliminations) | IFRS/VAS consolidation standards | N/A | ✅ Required |
| 10 | Uniform accounting policies across group | VAS/IFRS consolidation guidance | N/A | ✅ Required |
| 11 | Software certification by Tổng cục Thuế | Nghị định 123/2024/NĐ-CP; Tổng cục Thuế software list | Per-company registration | N/A |

---

## Production Readiness Verdict

| Product | Multi-Company Production Ready? | Vietnamese Compliant? | Notes |
|---|---|---|---|
| **Fast Business Online** | ✅ YES | ✅ YES | Tổng cục Thuế-recognized; deployed for enterprise groups; has dedicated consolidation module |
| **Fast Accounting** | ❌ NO | ✅ YES (single-company) | Scales to enterprise; no multi-entity support |
| **MISA AMIS / ASP** | ❓ UNKNOWN | ✅ YES (single-company) | No confirmed multi-company accounting module found |
| **BravoERP** | ❓ UNKNOWN | ❓ UNKNOWN | Cannot assess — bravoerp.com returned no content |
| **Tryton** | ✅ YES (global) | ⚠️ PARTIAL | Core multi-company native; Vietnamese localization/language and VAS compliance would require custom development |

---

## Gaps / Risks

1. **No Vietnamese primary legal source confirmed** — gdt.gov.vn (Tổng cục Thuế) and vbpl.vn both errored/blocked during research. All legal conclusions based on published framework knowledge, not live fetch. Re-verify from official sources before final compliance sign-off.
2. **MISA ASP is service-layer, not multi-company accounting** — risk of confusing the platform (which connects businesses to accountants) with multi-entity accounting software.
3. **BravoERP unverifiable** — bravoerp.com returned no content. Product either has no public web presence or site is down. Do not use without direct vendor contact.
4. **Tryton has no Vietnamese locale** — deploying for Vietnamese compliance requires translation work, Tỷ giá configuration, Mẫu số customization, and BCTC template adaptation per Circular 99/2025/TT-BTC.
5. **Consolidated BCTC is only legally required for parent companies** — single-entity SMEs under the new micro-enterprise regime (Thông tư 58/2026/TT-BTC) are exempt from consolidation obligations. Multi-company is relevant only for group-structured enterprises.
6. **Big4 product guidance not publicly available** — EY/KPMG Vietnam sites show advisory service landing pages, not product evaluation guidance. Any vendor claims of "Big4 recommended" should be verified directly.
7. **IFRS for SMEs consolidation exception under review** — Exposure Draft (Sep 2026 deadline) may change requirements for subsidiary exemption from consolidation.

---

## Sources

| Source | URL | Status |
|---|---|---|
| FAST official | https://fast.com.vn | ✅ Accessible |
| FAST FBO product | https://fast.com.vn/phan-mem-erp-fast-business-online/ | ✅ Accessible |
| FAST Consolidated Reports | https://fast.com.vn/phan-mem-erp-fast-business-online-bao-cao-tai-chinh-hop-nhat-fast-consolidated-reports/ | ✅ Accessible |
| FAST Fast Accounting | https://fast.com.vn/phan-mem-ke-toan-fast-accounting/ | ✅ Accessible |
| MISA main | https://misa.com.vn | ✅ Accessible (no multi-company detail) |
| MISA AMIS Kế toán | https://amis.misa.vn/amis-ke-toan/ | ✅ Accessible (no multi-company detail) |
| MISA ASP | https://asp.misa.vn | ✅ Accessible (service marketplace) |
| BravoERP | https://bravoerp.com | ❌ No readable content |
| BravoERP alt | https://www.bravoerp.com | ❌ No readable content |
| Tryton docs home | https://docs.tryton.org | ✅ Accessible |
| Tryton Company module | https://docs.tryton.org/latest/modules-company/ | ✅ Accessible |
| Tryton Company design | https://docs.tryton.org/latest/modules-company/design.html | ✅ Accessible |
| Tổng cục Thuế | https://gdt.gov.vn | ❌ Transport error |
| Văn bản pháp luật | https://vbpl.vn | ❌ 403 Forbidden |
| Bộ Tài chính | https://www.mof.gov.vn | ✅ Accessible (portal only) |
| BHXH Vietnam | https://baohiemxahoi.gov.vn | ✅ Accessible (no multi-company content) |
| Customs Vietnam | https://customs.gov.vn | ✅ Accessible (portal only) |
| dịch vụ công | https://dichvucong.gov.vn | ✅ Accessible (portal only) |
| VAA | https://vaa.net.vn | ✅ Accessible |
| IFRS Foundation | https://www.ifrs.org | ✅ Accessible |
| IFRS for SMEs / consolidation ED | https://www.ifrs.org/projects/work-plan/ifrs-for-smes-accounting-standard-consolidation-exception/ | ✅ Active (comments due 09 Sep 2026) |
| EY Vietnam | https://www.ey.com/en_vn | ✅ Accessible |
| KPMG Vietnam | https://home.kpmg/vn | ❌ URL failed (should be kpmg.com/vn) |
| KPMG Vietnam (corrected) | https://kpmg.com/vn | ✅ Accessible |
| PwC Vietnam | N/A | ❌ Not fetched (URL error) |
| Deloitte Vietnam | N/A | ❌ Not fetched (URL error) |
