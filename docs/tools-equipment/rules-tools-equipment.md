# Business Rules — Tools & Equipment (CCDC) Module

## BR-001: CCDC Recognition Criteria
**Source:** Điều 26 TT200/2014/TT-BTC (applied via TT99/2025/TT-BTC)
- CCDC = tư liệu lao động KHÔNG đủ tiêu chuẩn ghi nhận TSCĐ
- TSCĐ criteria: value ≥ VND 5,000,000 AND useful life ≥ 12 months
- → CCDC: value < VND 5,000,000 OR useful life < 12 months

## BR-002: Account Mapping
**Source:** TT200/2014/TT-BTC Điều 26, TT99/2025/TT-BTC
| CCDC Type | Purchase Account | Allocation Account |
|-----------|-----------------|-------------------|
| CCDC dùng 1 kỳ | 1531 | → 623/627/641/642 (trực tiếp) |
| CCDC dùng nhiều kỳ | 1531 → 242 | → 623/627/641/642 (hàng tháng) |
| Bao bì luân chuyển | 1532 | → 623/627/641/642 (phân bổ) |
| Đồ dùng cho thuê | 1533 | → 623/627/641/642 (phân bổ) |

## BR-003: Allocation Period
**Source:** Điều 26 TT200/2014/TT-BTC, Luật Thuế TNDN
- Thời gian phân bổ tối đa: **3 năm** (36 tháng)
- Phân bổ đều hàng tháng
- Ngày bắt đầu phân bổ = ngày ghi tăng CCDC

## BR-004: Small Value Treatment
**Source:** Điều 26 TT200/2014/TT-BTC khoản 1.4
- CCDC có giá trị nhỏ khi xuất dùng: ghi nhận toàn bộ một lần vào chi phí
- Ngưỡng建议: ≤ VND 1,000,000 (doanh nghiệp tự quy định trong quy chế kế toán)

## BR-005: VAT Treatment
**Source:** Luật GTGT 2024 (Đ.14), NĐ 181/2025
- CCDC mua có HĐGTGT: GTGT đầu vào được khấu trừ (nếu đủ điều kiện)
- CCDC có giá trị < VND 5,000,000: cần chứng từ thanh toán không dùng tiền mặt để được khấu trừ VAT (Luật GTGT 2024)

## BR-006: Tax Deduction
**Source:** Luật Thuế TNDN, NĐ 174/2025
- Chi phí CCDC phân bổ được trừ khi xác định thu nhập chịu thuế
- Thời gian phân bổ tối đa 3 năm (không tính theo thời gian h会计)

## BR-007: Data Retention
**Source:** Luật Kế toán 2015 Art. 11
- Sổ CCDC phải lưu trữ **10 năm** kể từ cuối năm tài chính
- Bao gồm: sổ chi tiết, chứng từ, bảng phân bổ

## BR-008: Checksum Chain
**Source:** Internal (audit trail requirement)
- Mỗi CCDC có audit_checksum
- Checksum = SHA256(prev_checksum|id|action|actor|reason|timestamp)
- Genesis checksum = "0" * 64

## BR-009: RBAC
| Action | ADMIN | ACCOUNTANT | CHIEF_ACCOUNTANT | AUDITOR |
|--------|-------|------------|------------------|---------|
| Create CCDC | ✅ | ✅ | ✅ | ❌ |
| Modify CCDC | ✅ | ✅ | ✅ | ❌ |
| Deactivate CCDC | ❌ | ❌ | ✅ | ❌ |
| Reactivate CCDC | ❌ | ❌ | ✅ | ❌ |
| Write-off CCDC | ❌ | ❌ | ✅ | ❌ |
| Run allocation | ✅ | ✅ | ✅ | ❌ |
| Read CCDC | ✅ | ✅ | ✅ | ✅ |

## BR-010: Validation Rules
| Rule | Description | Error Code |
|------|-------------|------------|
| VR-001 | Code format `[A-Z0-9-]{2,50}` | EX-001 |
| VR-002 | purchase_price > 0 | EX-002 |
| VR-003 | useful_life_months: 1–36 | EX-003 |
| VR-004 | salvage_value < purchase_price | EX-004 |
| VR-005 | expense_account_code ∈ {623, 627, 641, 642} | EX-005 |
| VR-006 | If useful_life > 1, prepaid_account = 242 | EX-006 |
| VR-007 | Code immutable after creation | EX-007 |
| VR-008 | Cannot deactivate with pending allocations | EX-008 |
| VR-009 | Write-off requires completed allocations | EX-009 |
| VR-010 | Category ∈ CCDCCategory enum | EX-010 |

## BR-011: Allocation Object Distribution
**Source:** MISA AMIS reference
- Cho phép phân bổ CCDC cho nhiều đối tượng theo tỷ lệ (%)
- Tổng tỷ lệ phân bổ = 100%
- Đối tượng phân bổ: cost_center, dimension_value, hoặc cả hai
