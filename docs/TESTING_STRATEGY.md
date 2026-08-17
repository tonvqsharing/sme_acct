# Testing Strategy — Ứng dụng Kế toán SME (sme_acct)

| | |
|---|---|
| **Phiên bản** | 1.0 (draft) |
| **Ngày** | 2026-08-17 |
| **Trạng thái** | Chờ team review |
| **Phạm vi** | Backend Flask + SQLAlchemy + Frontend Jinja/Bulma/HTMX/Vanilla JS |
| **Đối tượng** | Toàn bộ dev + QA (team 3–10 người) |

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Mục tiêu và non-goals](#2-mục-tiêu-và-non-goals)
3. [Phân tích rủi ro](#3-phân-tích-rủi-ro)
4. [Mô hình testing tổng thể](#4-mô-hình-testing-tổng-thể)
5. [Chiến lược theo từng loại test](#5-chiến-lược-theo-từng-loại-test)
6. [Nên test gì, không nên test gì](#6-nên-test-gì-không-nên-test-gì)
7. [Chiến lược test automation](#7-chiến-lược-test-automation)
8. [Tích hợp testing vào CI/CD](#8-tích-hợp-testing-vào-cicd)
9. [Chiến lược dữ liệu test](#9-chiến-lược-dữ-liệu-test)
10. [Chiến lược môi trường test](#10-chiến-lược-môi-trường-test)
11. [Quản lý flaky test](#11-quản-lý-flaky-test)
12. [Metrics và chỉ số đo lường](#12-metrics-và-chỉ-số-đo-lường)
13. [Vai trò và trách nhiệm](#13-vai-trò-và-trách-nhiệm)
14. [Công cụ đề xuất](#14-công-cụ-đề-xuất)
15. [Lộ trình áp dụng](#15-lộ-trình-áp-dụng)
16. [Checklist testing strategy](#16-checklist-testing-strategy)
17. [Anti-patterns cần tránh](#17-anti-patterns-cần-tránh)
18. [Nguồn tham khảo](#18-nguồn-tham-khảo)

---

## 1. Tổng quan

### 1.1 Mục tiêu tài liệu

Tài liệu này định nghĩa **cách team test để giảm rủi ro**, không phải để "cho đủ test". Mục tiêu vận hành:

- Giảm bug lọt ra production (đặc biệt lỗi liên quan tiền, thuế, số liệu kế toán).
- Tăng tốc feedback: dev biết code sai trong phút, không phải trong ngày.
- Giảm chi phí: test viết 1 lần, chạy nhiều lần, ít phải bảo trì, ít flaky.
- Có CI/CD đáng tin: pipeline chạy đúng, kết quả đáng tin, không bị "đèn đỏ giả".

### 1.2 Phạm vi áp dụng

- Toàn bộ codebase `src/` (domain, application, infrastructure, presentation) và frontend (Jinja template, HTMX, Vanilla JS).
- Toàn bộ pipeline: commit → PR → merge → staging → release.
- KHÔNG bao gồm: quy trình quản lý yêu cầu, thiết kế hệ thống, vận hành hạ tầng (chỉ đề cập khi ảnh hưởng trực tiếp đến độ ổn định của test).

### 1.3 Nguyên tắc cốt lõi

1. **Test theo rủi ro** — tiền dồn vào chỗ dễ vỡ, dễ gây hại nhất.
2. **Test sớm, fail fast** — lỗi phát hiện ở tầng thấp rẻ hơn nhiều lần tầng cao.
3. **Automation đúng chỗ** — unit/integration là xương sống; E2E chỉ cho luồng quan trọng; manual chỉ cho phần máy không làm được.
4. **Ổn định hơn phong phú** — bộ test 100 test chạy xanh 100% lần còn giá trị hơn 1000 test flaky.
5. **Test là tài sản chung** — mọi thành viên viết, sửa, review test; không phải "việc của QA".
6. **Không chạy theo coverage 100%** — coverage là tham chiếu, không phải KPI.
7. **Chi phí hợp lý với team 3–10 người** — mọi thứ phải duy trì được bằng nguồn lực hiện có.

### 1.4 Giả định và thông tin chưa xác nhận

Tài liệu viết trên các giả định sau. Nếu giả định sai, điều chỉnh mục tương ứng:

| # | Giả định | Ảnh hưởng nếu sai |
|---|---|---|
| A1 | CI dùng **GitHub Actions** (repo hiện chưa có workflow — mục 8 vẽ pipeline giả định trên nền này). | Chuyển cấu hình sang GitLab CI/CircleCI, logic gating giữ nguyên. |
| A2 | E2E đang chạy bằng **Playwright** (theo thông tin đầu vào), bộ E2E hiện hữu nhưng **flaky**; chưa có Playwright trong `pyproject.toml` dev-deps. | Nếu E2E là công cụ khác, giữ nguyên chiến lược, thay lệnh chạy. |
| A3 | **Jest** dự kiến cho phần JS tương lai; hiện JS là Vanilla/HTMX nên chưa cần. | Khi có SPA/component JS, bổ sung tầng Jest — mục 5.2. |
| A4 | Production DB là MySQL/MariaDB hoặc PostgreSQL; SQLite chỉ dùng dev + test nhanh. | Nếu production cũng SQLite, bỏ job test chéo DB (mục 5.3), đơn giản hơn. |
| A5 | Release theo sprint (2–4 tuần), có staging environment riêng. | Nếu chưa có staging, mục 10 nêu cách dựng tối thiểu. |
| A6 | Số test hiện tại ~80 (pytest collect), chưa có coverage gate, chưa có contract test, chưa có security scan trong CI. | Số liệu là tham chiếu tại thời điểm viết. |
| A7 | Mỗi sprint có ít nhất 1 buổi "hardening" nhỏ (0.5–1 ngày) để xử lý nợ kỹ thuật test/flaky. | Nếu không có, roadmap mục 15 phải kéo dài. |

---

## 2. Mục tiêu và non-goals

### 2.1 Testing hướng đến điều gì

- Phát hiện lỗi **trước khi chạm tay người dùng**, đặc biệt: sai số tiền, sai thuế, sai trạng thái nghiệp vụ, mất dữ liệu, lỗi phân quyền.
- Làm cho **release an toàn và nhanh hơn** — release là quyết định dựa trên bằng chứng, không phải "cầu nguyện".
- Giữ **chi phí bảo trì test thấp** — mỗi test mới phải trả lời được "cái này bắt được lỗi gì mà test cũ không bắt được?".
- Xây dựng **sự tin tưởng của team vào test suite** — test xanh = code đúng, không phải "may mà xanh".

### 2.2 Non-goals (testing KHÔNG chịu trách nhiệm)

- Không đảm bảo **tuyệt đối** không có bug — mục tiêu là giảm rủi ro, không phải loại bỏ rủi ro.
- Không thay thế **review code, giám sát production (monitoring), backup dữ liệu** — đây là các tuyến phòng thủ khác, phải chạy song song.
- Không kiểm chứng **nghiệp vụ kế toán do thiếu spec rõ** — test chỉ kiểm chứng được theo đúng spec; spec sai thì test đúng cũng vô ích.
- Không phải **KPI hình thức** — chạy test để đạt chỉ số mà không giảm bug là thất bại.

### 2.3 Kỳ vọng thực tế

| Kỳ vọng | Mức thực tế |
|---|---|
| Unit + integration test chạy xong trong CI | **< 10 phút** (mục tiêu) |
| E2E critical flows chạy xong | **< 15 phút** (mục tiêu), giai đoạn đầu không chặn merge |
| Tỷ lệ flaky | **< 2%** số lượt chạy; test flaky phải vào backlog xử lý trong sprint |
| Bug nghiêm trọng lọt production | Giảm dần theo quý; mục 12 đo, không hứa con số cứng ngay |
| Coverage | Tham chiếu: domain ≥ 80% branch; còn lại không gate |

---

## 3. Phân tích rủi ro

### 3.1 Bản đồ rủi ro

Sản phẩm kế toán cho SME: người dùng là kế toán viên, giám đốc. Hậu quả lỗi không chỉ là bug UI mà còn **sai báo cáo thuế, sai sổ sách, vi phạm pháp lý, mất lòng tin khách hàng**.

| Khu vực | Rủi ro chính | Ảnh hưởng | Khả năng xảy ra | Ưu tiên test |
|---|---|---|---|---|
| **Tính toán tiền** (Invoice subtotal/VAT/tổng, Voucher cân đối nợ-có) | Sai phép tính, làm tròn, sai ngày | Rất cao — sai tiền, sai thuế | Cao | ★★★★★ |
| **Quy tắc nghiệp vụ domain** (MST, mã tài khoản, trạng thái Company: active/suspended/dissolved) | Bỏ qua ràng buộc, cho phép chuyển trạng thái bất hợp lệ | Cao — dữ liệu kế toán sai chuẩn pháp lý | Cao | ★★★★★ |
| **Dữ liệu trùng/duy nhất** (MST trùng → 409) | Race condition, thiếu unique constraint | Cao — hồ sơ doanh nghiệp lẫn lộn | Trung bình | ★★★★ |
| **Phân quyền & xác thực** (login, pycasbin RBAC) | Người dùng thấy/sửa dữ liệu người khác | Rất cao — lộ số liệu tài chính | Trung bình | ★★★★★ |
| **Lưu trữ & migration DB** (flask-migrate, JSON column, enum) | Mất dữ liệu khi upgrade, sai kiểu dữ liệu giữa DB | Rất cao | Trung bình | ★★★★ |
| **Khác biệt DB dialect** (SQLite dev vs MySQL/PG prod) | Logic chạy đúng trên SQLite, sai trên production | Cao | Trung bình | ★★★ |
| **Luồng người dùng quan trọng** (tạo công ty → lập hóa đơn → ghi sổ → báo cáo) | Vỡ luồng end-to-end do tích hợp tầng | Cao | Trung bình | ★★★★ |
| **UI/UX** (form validation, thông báo lỗi, HTMX tương tác) | Người dùng nhập sai mà không biết | Trung bình | Cao | ★★ |
| **Hiệu năng** (báo cáo, sổ cái trên dữ liệu lớn) | Báo cáo chậm, timeout | Trung bình | Thấp-Trung bình | ★★ |
| **Bảo mật** (SQLi, XSS, CSRF, lộ dữ liệu qua API) | Lộ/đánh cắp dữ liệu tài chính | Rất cao | Thấp | ★★★★ (khác tầng) |

### 3.2 Nguyên tắc ưu tiên theo rủi ro

```
  Lỗi liên quan TIỀN / THUẾ / TRẠNG THÁI NGHIỆP VỤ?
      |
      |-- CÓ --> Test tự động, nhiều, sâu, ở tầng THẤP (unit + integration)
      |          (rẻ, nhanh, bắt lỗi đúng gốc)
      |
      |-- KHÔNG
           |
           Lỗi do TÍCH HỢP nhiều module / DB / API?
              |
              |-- CÓ --> Integration test + API test (chạy trên CI)
              |
              |-- KHÔNG
                   |
                   Lỗi ở LUỒNG NGƯỜI DÙNG quan trọng?
                      |
                      |-- CÓ --> E2E test (Playwright, SỐ LƯỢNG ÍT, chỉ critical)
                      |
                      |-- KHÔNG --> Cân nhắc không test hoặc test thủ công nhẹ
```

**Hệ quả trực tiếp:** phần lớn test tập trung vào `src/domain/` và `src/application/` (tính toán, quy tắc, trạng thái) + `src/infrastructure/` + `src/presentation/api/` (tích hợp). UI chi tiết test ít.

---

## 4. Mô hình testing tổng thể

### 4.1 Pyramid tùy biến cho dự án này

Pyramid kinh điển (Google/Fowler) là nền, nhưng vì là **web app monolith Flask** với logic nghiệp vụ tập trung ở domain layer thuần Python, team dùng biến thể sau:

```
        [E2E - Critical flows]     ~10-15 test   Playwright
              /\
             /  \
            /    \
   [API / Contract test]           ~60-80 test   pytest + Flask test client
          /        \
         /          \
        /            \
[Integration test]              ~40-60 test   pytest + SQLite in-memory (repo + service)
       /              \
      /                \
     /                  \
[Unit test - Domain logic]      ~100-150 test  pytest (thuần, không DB, không web)
          |
          |
[Static checks]                 ruff + black + mypy (strict) + secret scan
```

**Tỷ lệ mục tiêu (tham khảo):** ~60% unit, ~30% integration/API, ~10% E2E — theo Google Testing Blog (70/20/10 là điểm khởi đầu, tùy sản phẩm, miễn giữ hình kim tự tháp).

### 4.2 Giải thích từng tầng

| Tầng | Trả lời câu hỏi | Tốc độ | Chi phí bảo trì | Độ tin cậy phát hiện lỗi |
|---|---|---|---|---|
| **Unit (domain)** | Logic tính toán/quy tắc có đúng không? | ms | Thấp | Cao cho lỗi logic |
| **Integration (repo/service)** | Dữ liệu lưu/đọc đúng không? Service xử lý đúng khi có DB thật? | giây | Trung bình | Cao cho lỗi tầng dữ liệu |
| **API/Contract** | API trả đúng contract (status, body, lỗi 4xx/5xx)? | giây | Trung bình | Cao cho lỗi tích hợp front-back |
| **E2E** | Luồng người dùng chạy thông suốt qua UI? | phút | Cao | Cao nhất cho tích hợp toàn hệ thống, nhưng dễ flaky |
| **Static** | Lint/type sai, secret bị lộ? | giây | Thấp nhất | Không bắt lỗi logic |

**Quy tắc di chuyển test xuống thấp hơn:** nếu một kịch bản E2E có thể kiểm chứng ở tầng API/integration, hãy viết ở tầng đó, chỉ giữ E2E khi giá trị của nó là **xác nhận luồng người dùng thật** (click, form, điều hướng, HTMX swap) mà API test không thấy được.

---

## 5. Chiến lược theo từng loại test

Ưu tiên: **MUST** = bắt buộc, **SHOULD** = nên, **MAY** = tùy theo tình huống.

### 5.1 Unit test — logic domain và service

- **Mục đích:** kiểm chứng quy tắc nghiệp vụ, tính toán, chuyển trạng thái, edge case — nơi lỗi tốn tiền nhất.
- **Khi nào dùng:** mọi logic thuần có nhánh điều kiện, phép tính, ràng buộc. Ví dụ trong repo này:
  - `TaxId` / `AccountCode` validation (regex MST `^\d{10}(-\d{3})?$`, mã tài khoản 3–4 chữ số).
  - `Invoice.add_item()` → subtotal/vat/grand_total tự tính lại.
  - `Voucher.post()` → cân đối nợ-có trong tolerance 0.01, chỉ post từ DRAFT.
  - `Company` status lifecycle: active → suspended/dissolved, cấm chuyển trạng thái bất hợp lệ.
- **Khi nào không nên lạm dụng:** đừng test getter/setter tầm thường, đừng test implementation detail (tên biến nội bộ, thứ tự gọi hàm), đừng mock quá sâu chỉ để "đủ coverage".
- **Công cụ:** pytest, `pytest.mark.parametrize` cho dải input (đặc biệt giá trị biên của tiền, ngày, MST). Mock bằng `unittest.mock` cho dependency ngoài (rất hiếm khi cần ở domain vì domain thuần).
- **Trade-off:** viết nhanh, chạy nhanh, nhưng chỉ kiểm chứng 1 đơn vị — không bắt lỗi tích hợp. Vì vậy không thay thế integration test.

**Ưu tiên: MUST** (cho domain + service; xem mục 6 về mức độ).

### 5.2 Unit test — JS frontend (Jest)

- **Mục đích:** kiểm chứng logic JS thuần (nếu có): format tiền, format ngày, tính toán trên form, xử lý dữ liệu HTMX response.
- **Khi nào dùng:** CHỈ khi code JS có logic đáng test. Hiện tại JS là Vanilla + HTMX mỏng → **chưa cần Jest**.
- **Khi nào áp dụng sau này:** khi xuất hiện module JS có nhánh logic (tính tiền tạm trên form, validation phía client, tiện ích dùng chung).
- **Công cụ:** Jest + Testing Library (nếu test DOM component).
- **Trade-off:** thêm một toolchain + quy tắc build; không thêm nếu không có logic JS thật.

**Ưu tiên: MAY** (hiện tại) → **SHOULD** khi JS có logic.

### 5.3 Integration test — repository + service + DB

- **Mục đích:** kiểm chứng **tích hợp thật** giữa domain/service với DB (SQLAlchemy model, constraint, transaction, enum mapping, JSON column).
- **Khi nào dùng:** mọi thao tác đọc/ghi DB quan trọng. Hiện repo đã có pattern đúng: `tests/integration/test_company_repository.py` (in-memory SQLite, không cần Flask app context) và `test_company_api.py` (Flask test client + engine riêng). Chuẩn hóa và nhân rộng pattern này.
- **Điểm quan trọng với dự án này:** SQLite ≠ MySQL/PostgreSQL ở JSON, enum, collation, unique constraint, kiểu date. → **Chạy ít nhất 1 job CI chéo DB** (MySQL hoặc PostgreSQL) cho bộ integration test, theo lịch định kỳ + trước release (xem mục 8). Không chạy trên mọi commit (chi phí).
- **Khi nào không nên:** không dùng integration test cho logic thuần (phí thời gian), không test qua UI.
- **Công cụ:** pytest + SQLAlchemy + SQLite `:memory:` (nhanh), MySQL/PG chạy bằng Docker service trong CI.
- **Trade-off:** chậm hơn unit (giây), cần cơ chế reset DB sạch giữa các test → nếu reset kém sẽ sinh flaky do nhiễm state.

**Ưu tiên: MUST.**

### 5.4 API / Contract test

- **Mục đích:** kiểm chứng hợp đồng giữa frontend (Jinja/HTMX gọi API) và backend: status code, cấu trúc JSON, mã lỗi chuẩn (`MST_TAKEN`, `NOT_FOUND`...), trạng thái 400/401/403/404/409/422.
- **Khi nào dùng:** mọi endpoint REST dùng bởi frontend hoặc tích hợp ngoài. Hiện có sẵn trong `test_company_api.py` — bổ sung theo từng module.
- **Khi nào không nên:** đừng viết test trùng lặp 100% với integration test; contract test tập trung vào **giao diện API** (status, body, lỗi), integration test tập trung vào **hành vi dữ liệu**.
- **Công cụ:** pytest + Flask test client (đủ cho monolith nội bộ). Nếu sau này có client ngoài (mobile, đối tác), nâng lên **OpenAPI spec + schema validation** (ví dụ `jsonschema`/`schemathesis` cho fuzzing contract).
- **Trade-off:** bảo trì thêm khi đổi API; nhưng bắt được lỗi "frontend gửi sai, backend trả sai" sớm hơn E2E rất nhiều.

**Ưu tiên: MUST.**

### 5.5 E2E test — Playwright

- **Mục đích:** xác nhận **luồng người dùng quan trọng** chạy thông suốt qua UI thật (click, điền form, HTMX swap, điều hướng, thông báo).
- **Khi nào dùng:** CHỈ cho critical journeys. Đề xuất bộ đầu tiên (8–12 spec):
  1. Đăng nhập / đăng xuất / session hết hạn.
  2. Phân quyền: user không có quyền không vào được trang/API.
  3. Onboarding tạo doanh nghiệp (company) — validate MST trùng hiện lỗi 409 đẹp trên UI.
  4. Lập hóa đơn → tổng tiền/subtotal/VAT hiển thị đúng trên form.
  5. Ghi sổ chứng từ → cân đối nợ-có → báo lỗi khi lệch.
  6. Chuyển trạng thái công ty active → suspended → khóa.
  7. Xem một báo cáo kế toán cơ bản (không verify con số chi tiết — việc của unit/integration; chỉ verify luồng hiển thị).
- **Khi nào không nên:** không dùng E2E để test edge case số liệu, không test toàn bộ form validation (làm ở API test), không test mọi trạng thái nghiệp vụ (làm ở unit). E2E vỡ → debug tốn giờ → là nguồn flaky chính.
- **Thực hành bắt buộc (theo Playwright docs):** web-first assertions (`toBeVisible`, `toHaveText`...) thay vì manual assertions; locator ưu tiên role/label/text, tránh CSS phụ thuộc layout; không dùng `sleep`; `workers: 1` trong CI (độ ổn định) trước khi shard; `retries: 2` trên CI; `forbidOnly` để chặn `test.only` lọt; `trace: on-first-retry` để debug.
- **Công cụ:** Playwright (default), chỉ chạy Chromium trong CI (chi phí), Firefox/WebKit chạy cục bộ khi cần.
- **Trade-off:** chi phí viết + bảo trì cao nhất, dễ flaky → **số lượng ít, chỉ critical**, và giai đoạn đầu **không chặn merge** (mục 8).

**Ưu tiên: MUST** (nhưng giới hạn số lượng và không gating ngay).

### 5.6 Manual exploratory test

- **Mục đích:** tìm lỗi mà automation không thiết kế trước được: luồng bất thường, UX xấu, dữ liệu lạ, tương tác chéo module.
- **Khi nào dùng:**
  - Trước release (mỗi sprint): **1 phiên exploratory có hướng dẫn (charter)**, 1–2 giờ, người không phải tác giả chức năng.
  - Sau khi thay đổi lớn về nghiệp vụ / migration DB.
  - Khám phá module mới lần đầu (trước khi viết automation — cách tốt nhất để biết test gì).
- **Khi nào không nên:** không dùng manual cho regression lặp lại — cái đó phải tự động. Không dùng manual để "bù" cho E2E flaky.
- **Công cụ:** checklist charter trong issue tracker; ghi bug kèm bước tái hiện + dữ liệu.

**Ưu tiên: MUST** (nhẹ, theo charter), **SHOULD** khi team đông.

### 5.7 Performance test

- **Mục đích:** đảm bảo nghiệp vụ nặng (báo cáo, sổ cái, tổng hợp theo kỳ) không timeout/không chậm bất thường khi dữ liệu tăng.
- **Khi nào dùng:** 
  - **Smoke performance (SHOULD):** 1–2 endpoint báo cáo quan trọng, dữ liệu seed ước lượng cỡ 1 năm hoạt động của khách lớn, kiểm tra thời gian phản hồi không vượt ngưỡng (ví dụ p95 < 3s). Chạy định kỳ hàng tuần trên staging.
  - **Load test đầy đủ (MAY):** chỉ khi có dấu hiệu vấn đề hoặc trước release lớn về báo cáo.
- **Khi nào không nên:** đừng build kịch bản load phức tạp ngay từ đầu — team 3–10 người, sản phẩm nội bộ SME, không phải hệ thống giao dịch cao tần.
- **Công cụ:** `locust` (đơn giản, Python) hoặc k6. Smoke bằng script pytest đơn giản cũng đủ giai đoạn đầu.
- **Trade-off:** seed dữ liệu + hạ tầng chạy tốn công; bắt đầu từ smoke rồi mở rộng khi có bằng chứng cần.

**Ưu tiên: SHOULD** (smoke) / **MAY** (load đầy đủ).

### 5.8 Security test

Sản phẩm tài chính → security không phải "nếu có", mà là **bắt buộc tối thiểu**. Chia 3 mức:

| Mức | Nội dung | Tần suất | Ưu tiên |
|---|---|---|---|
| **A. Tự động trong CI** | Quét dependency lỗ hổng (`pip-audit`), quét secret trong repo (trufflehog/gitleaks), test tự động cho: phân quyền truy cập API (403 khi thiếu quyền), CSRF trên form, header an toàn (Talisman), nhập liệu độc hại (MST/SQL injection qua API) | Mọi PR (dependency) + định kỳ | **MUST** |
| **B. Rà soát theo checklist OWASP WSTG** | XSS, SQLi, auth/session, IDOR (truy cập object người khác qua id), nhạy cảm dữ liệu response | Mỗi release lớn, người hiểu bảo mật thực hiện | **SHOULD** |
| **C. Pentest chuyên sâu** | Thuê ngoài / công cụ chuyên dụng | Khi có khách hàng lớn / yêu cầu tuân thủ | **MAY** |

- **Khi nào không nên:** đừng đợi đến lúc có "chuyên gia bảo mật" mới làm mức A — mức A là việc của dev hàng ngày.
- **Công cụ:** `pip-audit`, `gitleaks`/`trufflehog`, OWASP WSTG làm checklist tham chiếu. ZAP baseline scan (MAY) cho staging.

**Ưu tiên: A=MUST, B=SHOULD, C=MAY.**

### 5.9 Accessibility test

- **Mục đích:** người dùng thật gồm kế toán viên nhiều độ tuổi, có thể dùng công cụ hỗ trợ (screen reader, phóng to).
- **Khi nào dùng:** kiểm tra cơ bản bằng **axe-core gắn vào Playwright** cho các trang chính (label đầy đủ cho form, contrast, heading hierarchy) — chi phí rất thấp khi đã có Playwright.
- **Khi nào không nên:** chưa cần kiểm thử a11y chuyên sâu với người khuyết tật thật ở giai đoạn này.
- **Công cụ:** `@axe-core/playwright`.
- **Trade-off:** thêm ~vài phút vào E2E; lợi ích vượt chi phí.

**Ưu tiên: SHOULD** (cơ bản, gắn E2E) / **MAY** (chuyên sâu).

### 5.10 Tổng hợp ưu tiên

| Loại test | Ưu tiên | Chặn merge? | Chạy ở đâu |
|---|---|---|---|
| Unit (domain/service) | MUST | Có | PR + commit |
| Integration (repo/DB) | MUST | Có | PR |
| API/Contract | MUST | Có | PR |
| Static (ruff/black/mypy/secret) | MUST | Có | PR |
| E2E critical (Playwright) | MUST (giới hạn số lượng) | **GĐ đầu: không; sau khi ổn định: có** | Staging sau deploy |
| Unit JS (Jest) | MAY → SHOULD | (khi có) | PR |
| Performance smoke | SHOULD | Không (cảnh báo) | Định kỳ / staging |
| Security CI | MUST (mức A) | Có (dependency) | PR + định kỳ |
| Security manual (WSTG) | SHOULD (mức B) | Không | Trước release lớn |
| Accessibility (axe) | SHOULD | Không | E2E |
| Manual exploratory | MUST (nhẹ) | Không (báo cáo) | Trước release |

---

## 6. Nên test gì, không nên test gì

### 6.1 Test NHIỀU (sâu, đủ edge case)

- **Domain rules** — mọi quy tắc trong `src/domain/entities/`:
  - `TaxId`, `AccountCode` validation (đúng/sai/boundary: `\d{10}`, `\d{10}-\d{3}`, mã tài khoản 3/4 chữ số, ký tự lạ, rỗng).
  - `Invoice.add_item()`: tính lại subtotal/VAT/grand_total; thêm/xóa dòng; số âm; nhiều thuế suất.
  - `Voucher.post()`: cân đối trong tol 0.01; lệch 0.005 (làm tròn!); post từ trạng thái sai.
  - `Company` status lifecycle: mọi cặp chuyển trạng thái hợp lệ/bất hợp lệ, `config_version`, audit fields.
- **Service layer** — `PartnerService`, `InvoiceService`, `VoucherService`: nghiệp vụ điều phối, ném exception đúng (`NotFoundError`, `AlreadyExistsError`, `InvalidVoucher`...), thứ tự kiểm tra.
- **Ràng buộc dữ liệu** — trùng MST (409), khóa ngoại `company_id` khi xóa, unique constraint.
- **Error handling & validation** — mọi đường API trả 400/401/403/404/409/422 phải có test; lỗi phải có mã lỗi ổn định cho frontend bắt.
- **Phân quyền** — endpoint yêu cầu role X thì user role Y phải bị chặn (403) ở cả API và UI.
- **Migration** — lên/xuống giữa các bản migration trên DB sạch + DB có dữ liệu.

### 6.2 Test VỪA ĐỦ

- **Repository adapter** — test đường chính (create/read/update) + vài lỗi điển hình; không test từng tổ hợp của SQLAlchemy.
- **API handler** — test hợp đồng + lỗi chuẩn; không lặp lại test logic đã có ở service.
- **UI form validation** — xác nhận thông báo lỗi hiển thị cho 1–2 trường đại diện (E2E), phần còn lại đã test ở API.
- **Hiển thị số liệu** — E2E verify số hiện trên màn hình khớp 1 kịch bản mẫu; không verify toàn bộ phép tính trên UI.

### 6.3 KHÔNG nên test (hoặc tránh test trực tiếp)

- **Implementation details** — tên hàm nội bộ, thứ tự gọi, cấu trúc class. Test hành vi quan sát được, không test cách cài đặt → refactor không phải sửa test.
- **Getter/setter thuần, mapping 1-1 không logic** — SQLAlchemy column mapping tầm thường.
- **Từng dòng Jinja template** — template mỏng không cần test; hành vi hiển thị đi qua E2E.
- **Thư viện bên thứ ba** — không test Flask/SQLAlchemy/HTMX hoạt động ra sao (trừ khi nghi ngờ integration bug, thì viết 1 test tái hiện).
- **Toàn bộ luồng qua UI cho edge case nghiệp vụ** — đưa xuống API/unit, E2E chỉ giữ luồng chính.
- **Code chưa có spec rõ** — test sẽ đóng băng hành vi sai; viết test sau khi spec xong.

### 6.4 Decision tree chọn nơi test (dán cạnh bàn làm việc)

```
  Logic nghiệp vụ quan trọng (tiền/thuế/trạng thái)?
      |-- ĐÚNG --> Unit test (domain/service)
      |-- SAI
           |
           Đụng DB / nhiều module / API?
              |-- ĐÚNG --> Integration test + API test
              |-- SAI
                   |
                   Luồng người dùng quan trọng qua UI?
                      |-- ĐÚNG --> E2E (Playwright), ít, critical
                      |-- SAI --> Không test tự động hoặc test tay nhẹ
```

---

## 7. Chiến lược test automation

### 7.1 Nguyên tắc chọn test để automation

```
  Test này chạy LẶP LẠI sau mỗi thay đổi code?
      |-- KHÔNG --> Manual (exploratory), đừng tự động
      |-- CÓ
           |
           Có giá trị PHÁT HIỆN lỗi rõ ràng (không phải test hình thức)?
              |-- KHÔNG --> Không viết
              |-- CÓ
                   |
                   CHẠY ỔN ĐỊNH được không (không phụ thuộc thời gian/UI chi tiết)?
                      |-- KHÔNG --> Viết ở tầng thấp hơn hoặc bỏ
                      |-- CÓ --> Tự động hóa
```

### 7.2 Automation trước (thứ tự ưu tiên)

1. Static checks + unit test domain (rẻ nhất, bắt lỗi tiền).
2. Integration + API test (chặn lỗi tích hợp).
3. E2E critical flows (sau khi API test ổn định).
4. Security CI cơ bản (dependency + secret + phân quyền test).
5. Performance smoke.

### 7.3 Giữ manual

- Exploratory theo charter trước release.
- Kiểm tra nghiệp vụ cần phán đoán kế toán viên (số liệu có "hợp lý nghiệp vụ" không).
- UX/cảm nhận, layout, lỗi mỹ thuật (không phải lỗi chức năng).

### 7.4 Đặt tên test

- **pytest:** `test_<hành_vi>_<điều_kiện>` — ví dụ `test_post_voucher_rejects_unbalanced_entries`, `test_duplicate_mst_returns_409`. Tên đọc lên phải thành câu: "khi điều kiện X thì hành vi Y".
- **Playwright:** `tests/e2e/<module>.spec.ts`, test name theo luồng: `'tạo doanh nghiệp với MST trùng hiện lỗi'`.
- Dùng `@pytest.mark.parametrize` thay cho nhiều test trùng lặp.

### 7.5 Tổ chức test code

```
tests/
  unit/
    company/test_company_entity.py
    company/test_company_service.py
  integration/
    test_company_repository.py
    test_company_api.py
  api/            # contract test theo module (tách khỏi integration khi lớn)
  e2e/            # Playwright (riêng, không trộn pytest)
  factories.py    # builders dữ liệu dùng chung
  conftest.py     # fixtures dùng chung
```

- Test nằm cạnh module theo lớp (unit/integration/api), không trộn.
- `conftest.py` dùng chung fixtures: app test client, DB in-memory, factory builders (chuẩn hóa pattern `_make_kwargs` hiện có trong `test_company_api.py` thành module dùng chung).
- KHÔNG tạo class test khổng lồ nhiều trăm dòng setup — mỗi test tự cung cấp dữ liệu tối thiểu (Playwright: "keep tests independent").

### 7.6 Quản lý test data (tóm tắt — chi tiết mục 9)

- Dữ liệu tạo **trong test** bằng factory, không phụ thuộc dữ liệu có sẵn.
- Mỗi test tự reset state (fixture function-scoped).
- Không dùng dữ liệu thật của khách hàng (MST/STK/tên thật) trong test.

### 7.7 Xử lý flaky (tóm tắt — chi tiết mục 11)

- Phát hiện: CI ghi nhận test fail lại pass khi chạy lại.
- Chính sách: **Sửa → Cách ly → Xóa**, không chấp nhận flaky dài hạn.
- Không dùng retry để "giấu" — retry chỉ là công cụ chẩn đoán.

### 7.8 Không để test thành gánh nặng

- Test viết cùng PR với code (không để "sau", không làm sprint riêng).
- Nếu test tốn > 30 phút viết cho 1 hàm đơn giản → test đang sai tầng.
- Bộ test chậm → chạy song song (`pytest-xdist`), phân loại nhanh/chậm.
- Bảo trì test tính vào effort của feature, không phải "việc phát sinh".

---

## 8. Tích hợp testing vào CI/CD

### 8.1 Pipeline mục tiêu (GitHub Actions — giả định A1)

```
[Commit (local)]
    |  pre-commit hook: ruff + black --check + mypy (subset nhanh)
    v
[Push]
    v
[PR Checks - FAST GATE  (block merge)]
    |  1. ruff + black --check + mypy (strict)
    |  2. pip-audit (dependency lỗ hổng) + secret scan
    |  3. pytest unit + integration + API  (SQLite in-memory, < 10 phút)
    v
[Merge -> main]
    v
[Build + Deploy STAGING]
    v
[Staging Checks - giai đoạn đầu: NON-BLOCKING (cảnh báo)
                 sau khi ổn định: BLOCK release]
    |  4. E2E critical flows (Playwright, staging)
    |  5. Performance smoke (báo cáo quan trọng)
    |  6. axe-core accessibility (gắn E2E)
    |  7. Test chéo DB: integration trên MySQL/PG (Docker service)
    v
[Định kỳ hàng tuần / trước release]
    |  - Full E2E suite (nếu có bộ mở rộng)
    |  - WSTG checklist (mức B)
    v
[Release]
    |  - Manual exploratory theo charter
    |  - Quyết định release dựa trên: PR gate xanh + E2E xanh/đã cảnh báo
    |    + exploratory không có bug blocker
    v
[Production]
```

### 8.2 Chạy ở đâu, khi nào — chi tiết

| Giai đoạn | Test chạy | Block hay Warn | Lý do |
|---|---|---|---|
| **Commit (local)** | ruff, black, mypy, unit subset | Block (cá nhân) | Fail nhanh nhất, không tốn CI |
| **PR** | Static + secret + unit + integration + API | **Block merge** | Tuyến phòng thủ chính, < 10 phút |
| **PR** | pip-audit lỗ hổng mới | Block | Không merge code có dependency lỗ hổng |
| **Merge → Staging** | Build, migrate thử trên DB sạch, deploy | Block | Đảm bảo staging luôn khả dụng |
| **Staging (sau deploy)** | E2E critical, perf smoke, a11y | **GĐ đầu: Warn** → GĐ sau: Block | E2E hiện flaky; chặn ngay sẽ tê liệt team. Ổn định rồi mới chặn |
| **Hàng tuần** | Test chéo DB (MySQL/PG), full E2E | Warn + báo cáo | Bắt lỗi dialect, chi phí cao nên không chạy mỗi PR |
| **Trước release** | Full pipeline + WSTG mức B + exploratory | Chặn release nếu có blocker | Phòng thủ cuối |
| **Sau release** | Monitor (lỗi production, performance) | — | Phát hiện lỗi lọt → đưa về bộ test |

### 8.3 Quy tắc gating

- **PR gate là bắt buộc và phải nhanh (< 10 phút).** Nếu quá chậm: song song hóa, giảm test hình thức, chuyển test nặng xuống giai đoạn staging.
- **E2E chưa ổn định → không block merge ngay.** Tiêu chí chuyển sang block: E2E xanh liên tục **3 lần chạy liên tiếp** trên staging và flake rate < 2% (xem mục 11).
- **Không có "merge tạm thời bỏ qua test"** — nếu test fail thật (không phải flaky), PR không merge. Cách duy nhất là sửa code hoặc sửa test (nếu test sai).
- **Test fail liên tục không xác định được nguyên nhân → phải có người sở hữu ngay**, không để "đèn đỏ quen".

---

## 9. Chiến lược dữ liệu test

### 9.1 Các loại dữ liệu

| Loại | Dùng cho | Ví dụ trong dự án | Ưu tiên |
|---|---|---|---|
| **Dữ liệu cố định (fixtures)** | Test quy tắc có giá trị chuẩn hóa | MST hợp lệ `0123456789` / `0123456789-001` / sai `bad-mst`; mã tài khoản `111`, `6421` | MUST |
| **Factory / builder** | Tạo entity nhanh, override từng trường | Chuẩn hóa `_make_kwargs()` trong `test_company_api.py` thành `tests/factories.py` | MUST |
| **Dữ liệu sinh ngẫu nhiên** | Test tính duy nhất, song song, race | MST/Mã số sinh theo pattern hợp lệ + `uuid4` cho tên để E2E chạy song song không đụng nhau | SHOULD |
| **Mock/stub** | Cách ly dependency ngoài | Giả lập service gửi email/thông báo, gọi API ngoài (nếu có) | SHOULD (hạn chế — mock ít, integration nhiều) |
| **Dữ liệu thật ẩn danh hóa** | Staging giống production | Lấy cấu trúc dữ liệu thật, thay MST/STK/tên/địa chỉ bằng dữ liệu giả; **không bao giờ copy DB production có thông tin khách hàng** vào môi trường test | MUST (khi có dữ liệu thật) |

### 9.2 Reset database / state

```
Mỗi test:  state sạch, cô lập, không phụ thuộc thứ tự

  Unit test      -> không đụng DB (thuần)
  Integration    -> SQLite :memory: per test (pattern hiện có, giữ nguyên)
                     + transaction-rollback hoặc create_all/drop_all trong fixture
  API test       -> app test client + engine riêng (pattern test_company_api.py)
  E2E            -> trước suite: tạo DB mới + migrate + seed chuẩn
                     sau suite: xóa (không reuse state giữa các spec)
  Chéo DB (CI)   -> Docker service: khởi tạo schema bằng migration, chạy xong xóa
```

- **Không dùng chung DB giữa các test** (nhiễm state → flaky, theo Playwright: "keep tests independent").
- **Không phụ thuộc thứ tự chạy** — bất kỳ test nào cũng chạy được một mình (`pytest tests/unit/company/test_company_entity.py -k ...`).
- Migration test: chạy `flask db upgrade` từ 0 → hiện tại trên DB sạch, và downgrade từng bước, để bắt lỗi migration trước khi release.

### 9.3 Tránh phụ thuộc dữ liệu nhạy cảm

- Cấm dữ liệu thật: MST, số tài khoản ngân hàng, tên/CMND/địa chỉ khách hàng thật trong test hoặc fixture.
- Dữ liệu seed staging phải qua ẩn danh hóa; có quy trình kiểm tra (grep từ khóa nhạy cảm trong test data) — có thể đưa vào secret-scan step.

---

## 10. Chiến lược môi trường test

### 10.1 Các môi trường

| Môi trường | Mục đích | DB | Chủ sở hữu | Độ tin cậy kỳ vọng |
|---|---|---|---|---|
| **Local** | Dev viết test, debug | SQLite (file hoặc :memory:) | Dev | 100% cô lập |
| **CI** | PR gate, nhanh | SQLite :memory: + Docker service (chéo DB) | CI runner | Không phụ thuộc máy dev |
| **Staging** | E2E, perf smoke, exploratory, demo | MySQL/PG **giống production** (cùng version), dữ liệu ẩn danh hóa | Team (deploy tự động) | Phải luôn deploy được |
| **Production-like** (MAY) | Test migration với dữ liệu cỡ thật, load test | MySQL/PG, dữ liệu lớn | Khi có nhu cầu | Tách biệt staging |

### 10.2 Quy tắc chung

- **Test phải chạy được ở local bằng 1 lệnh**: `pytest` (unit+integration+API) — đã có sẵn qua `pyproject.toml`; E2E: `npx playwright test` với `webServer` config (Playwright tự khởi Flask server cho test).
- **Cấm test phụ thuộc môi trường cụ thể** của máy cá nhân: đường dẫn tuyệt đối, cổng cố định, biến môi trường thiếu. Dùng config mặc định + `conftest` cung cấp sẵn.
- **Biến môi trường test**: tách riêng (ví dụ `TESTING=1`, DB URI test); không dùng chung `instance/sme_acct.db` production với test.
- **Version dependency khóa chặt** qua `uv.lock` — CI và local cùng version → bớt "chạy được trên máy tôi".
- **Staging phải reproduce được từ code hiện tại**: build từ `main` mỗi lần merge; không ai sửa staging bằng tay.

---

## 11. Quản lý flaky test

### 11.1 Định nghĩa

Flaky test = test **cùng code, cùng input** nhưng lúc xanh lúc đỏ. Đây là **bug** (trong test hoặc trong môi trường/state), không phải "chuyện thường". Theo Google: test fail nhất quán còn tốt hơn test flaky — flaky giết chết niềm tin vào CI.

### 11.2 Nguyên nhân phổ biến trong dự án này

1. **Phụ thuộc timing** — chờ UI bằng `sleep`/timeout cứng (đặc biệt HTMX swap, request async). → Dùng web-first assertion của Playwright.
2. **State nhiễm giữa test** — dùng chung DB/engine/global, thứ tự chạy ảnh hưởng kết quả. → Cô lập per-test (mục 9.2).
3. **Locator yếu** — selector phụ thuộc CSS layout, text trùng. → Dùng role/label, `data-testid` cho phần phức tạp.
4. **Chạy song song không an toàn** — E2E đụng dữ liệu chung. → `workers: 1` trong CI trước, unique data khi cần song song.
5. **Môi trường không ổn định** — CI runner thiếu tài nguyên, network timeout. → Retry có kiểm soát + phân biệt lỗi hạ tầng và lỗi test.
6. **Assertion không chờ** — kiểm tra ngay khi element chưa sẵn sàng. → Web-first assertions, `expect.poll` khi cần.

### 11.3 Quy trình xử lý — chính sách Sửa / Cách ly / Xóa

```
[Test fail trên CI]
      |
      v
[Chạy lại 1 lần để chẩn đoán - KHÔNG giấu kết quả gốc]
      |
      +-- Fail lại (xác định) --> Xử lý như bug thật: sửa code hoặc sửa test
      |
      +-- Pass khi chạy lại (flaky)
           |
           v
[Gắn nhãn flaky + mở issue, ghi rõ: test nào, nguyên nhân nghi ngờ, ai sở hữu]
           |
           v
[Quyết định trong vòng 1-2 sprint]
   |-- SỬA   : tìm root cause (timing/state/locator) -> sửa -> chạy lại 10 lần xác nhận
   |-- CÁCH LY: gắn @pytest.mark.flaky (skip khỏi PR gate, vẫn chạy nền) 
   |             -> chỉ được tồn tại tối đa 1 sprint, sau đó phải sửa hoặc xóa
   |-- XÓA    : test không còn giá trị (bắt lỗi trùng test khác, setup quá phức tạp)
   |             -> xóa sạch, ghi chú lý do trong issue
```

### 11.4 Nguyên tắc

- **Không có retry tự động mặc định để "che" flaky.** Nếu có `retries` trong Playwright, nó phục vụ chẩn đoán (`trace: on-first-retry`), không phải để xem test là "pass".
- **Flaky không được tồn tại dài hạn** — cách ly là giải pháp tạm thời, không phải lối sống.
- **Chỉ số theo dõi:** tỷ lệ flake = số lượt fail-flaky / tổng lượt chạy. Mục tiêu < 2%. Flake rate tăng → ưu tiên xử lý trước khi thêm test mới.
- **Trách nhiệm:** tác giả test phải sửa test của mình (mục 13). Không đùn sang QA.
- **Nguyên nhân gốc trong production code cũng là bug:** Google ghi nhận ~1/6 trường hợp test trở nên flaky sau một code change là do bug production. Đừng vội đổ lỗi cho test.

---

## 12. Metrics và chỉ số đo lường

### 12.1 Chỉ số chính (theo dõi hàng sprint, nhìn xu hướng)

| Chỉ số | Định nghĩa | Mục tiêu | Nguồn dữ liệu |
|---|---|---|---|
| **Tỷ lệ bug production** | Số bug do khách báo / sprint (phân loại nghiêm trọng) | Giảm dần theo quý | Issue tracker + tag "production" |
| **Tỷ lệ bug lọt qua test** | Bug production mà đáng lẽ test tự động bắt được (cùng class lỗi đã có test tương tự) | < 10% số bug production | Review bug hàng tuần: "thêm test gì để bắt được cái này?" |
| **Thời gian feedback CI** | PR gate từ push → kết quả | p50 < 10 phút | CI log |
| **Tỷ lệ flaky** | Fail-flaky / tổng lượt chạy | < 2% | CI results |
| **Số test bị cách ly** | Đang mang nhãn flaky/cách ly | ≤ 0 (mục tiêu dài hạn), không tăng | CI + issue |
| **Lỗi nghiêm trọng phát hiện sớm** | Số bug P1/P2 bắt được ở test tự động / staging / exploratory trước production | Đa số P1/P2 bắt trước production | Issue tracker |
| **Niềm tin team vào test suite** | Khảo sát nhẹ mỗi quý: "khi test xanh, bạn có tin code đúng không?" (1–5) | ≥ 4 | Khảo sát |

### 12.2 Coverage — chỉ là tham chiếu

- Chỉ áp dụng gate coverage có ý nghĩa ở **domain layer** (nơi chứa rủi ro tiền): ≥ 80% branch. Các layer khác không gate.
- Coverage giảm đột ngột ở domain → cảnh báo trong PR, không tự động block.
- Không bao giờ viết test chỉ để "tăng coverage" — test phải assert hành vi, không assert dòng code chạy.

### 12.3 Quy tắc dùng metrics

- Metrics để **phát hiện xu hướng xấu** và **quyết định ưu tiên**, không phải để khen/chê cá nhân.
- Nếu bug production nhiều mà test vẫn xanh → test đang sai chỗ; quay lại mục 6 (test đúng rủi ro) trước khi viết thêm test.

---

## 13. Vai trò và trách nhiệm

| Ai | Viết / làm gì | Chịu trách nhiệm |
|---|---|---|
| **Developer (mọi thành viên)** | Unit test domain/service cho code mình viết; integration + API test cho module mình làm; sửa test của mình khi flaky; chạy test trước khi push | Code đúng + test đi kèm PR |
| **QA / SDET** | E2E critical flows (Playwright); exploratory test; chiến lược test data; flake triage; metrics; review chất lượng bộ test; đề xuất test mới cho bug production lặp lại | Bộ test đáng tin, pipeline xanh ổn định |
| **DevOps / tech lead** | Pipeline CI/CD, cấu hình gating, môi trường staging, test chéo DB | CI ổn định, staging khả dụng |
| **Tác giả test** | Sửa test flaky của mình; xóa test vô giá trị | Không để flaky tồn tại dài |
| **Reviewer** | Review test cùng code trong PR: test có ý nghĩa không, có test đúng tầng không, có flaky-prone không | Chất lượng PR |
| **Tech lead / PM** | Quyết định release dựa trên: PR gate xanh, E2E ổn định, exploratory không có blocker, metrics không cảnh báo | Quyết định release |

Nguyên tắc: **ai cũng viết test** — không phải "chỉ QA". QA không phải người duy nhất bảo vệ chất lượng; họ là người xây dựng hệ thống phòng thủ và giữ nó vận hành.

---

## 14. Công cụ đề xuất

### 14.1 Backend (Python) — đã có sẵn trong `pyproject.toml`

| Việc | Công cụ (mặc định) | Ghi chú |
|---|---|---|
| Unit + integration + API test | **pytest** + `pytest-cov` | Đã cấu hình (`testpaths`, `pythonpath`) |
| Chạy song song (khi bộ test lớn) | `pytest-xdist` | MAY, khi unit+integration > 5 phút |
| Mock | `unittest.mock` (stdlib) | Đủ dùng |
| Coverage | `pytest-cov` | Gate riêng domain |
| Lint / format / type | **ruff**, **black**, **mypy** (strict) | Đã có, là một phần của PR gate |
| Quét dependency | `pip-audit` | MUST trong CI |
| Quét secret | `gitleaks` hoặc `trufflehog` | MUST trong CI |

### 14.2 Frontend E2E — Playwright (default)

| Việc | Công cụ | Ghi chú |
|---|---|---|
| E2E | **Playwright Test** | Web-first assertions, trace, `webServer` khởi Flask |
| Accessibility | `@axe-core/playwright` | Gắn vào E2E |
| JS unit (tương lai) | **Jest** + Testing Library | Chỉ khi có logic JS thật (giả định A3) |

### 14.3 Security & performance

| Việc | Công cụ | Mức |
|---|---|---|
| Quét dependency + secret | `pip-audit` + `gitleaks` | MUST |
| Checklist bảo mật thủ công | **OWASP WSTG** (v4.2 stable) | SHOULD |
| Quét staging tự động | OWASP ZAP (baseline scan) | MAY |
| Performance smoke / load | `locust` hoặc k6 | SHOULD (smoke) / MAY (load) |

### 14.4 Không dùng / tránh

- Không thêm framework test song song trùng chức năng (không pytest + unittest + nose cùng lúc).
- Không dùng record-playback tool cho E2E (sinh test dễ vỡ, khó bảo trì — Fowler đã chỉ rõ từ lâu).
- Không cài tool báo cáo test phức tạp khi team chưa cần; GitHub Actions checks + issue tracker là đủ.

---

## 15. Lộ trình áp dụng

### 15.1 Roadmap

```
[G0: Hiện trạng]
   ~80 test pytest (unit + integration + API)
   E2E có nhưng flaky, CI chưa ổn định, chưa có workflow trong repo
      |
      v
[G1: Nền tảng tối thiểu (sprint 1-2)]
   CI GitHub Actions: ruff + black + mypy + secret + unit + integration + API
   E2E hiện có: chạy lại, phân loại flaky, tách khỏi gating
   Chuẩn hóa factories + conftest; pip-audit
   = Tiêu chí thoát: PR gate xanh ổn định, E2E không chặn merge
      |
      v
[G2: Test critical flows (sprint 2-4)]
   Playwright: 8-12 E2E critical (theo mục 5.5)
   API contract test cho toàn bộ endpoint hiện có
   Security: test phân quyền tự động + pip-audit gating
   Coverage gate domain >= 80% branch
   = Tiêu chí thoát: E2E xanh 3 lần liên tiếp, flake < 2%
      |
      v
[G3: CI/CD ổn định + giảm flaky (sprint 4-6)]
   E2E chuyển sang block release (sau khi ổn định)
   Test chéo DB MySQL/PG hàng tuần; performance smoke
   Flaky policy vận hành (mục 11); metrics dashboard
   = Tiêu chí thoát: release qua pipeline, flake < 2% duy trì 2 sprint
      |
      v
[G4: Đo lường + cải tiến liên tục]
   Metrics hằng sprint (mục 12); review bug lọt -> bổ sung test
   WSTG mức B trước release lớn; exploratory theo charter
   Tinh chỉnh tỷ lệ pyramid theo dữ liệu bug thật
```

### 15.2 Lưu ý thực thi

- **Mỗi giai đoạn phải có "tiêu chí thoát" đo được** (như trên) — không nhảy giai đoạn khi chưa đạt.
- G1 là **ưu tiên tuyệt đối**: nền CI không ổn định thì mọi thứ sau đều xây trên cát. Đừng viết E2E mới khi CI đang đỏ thất thường.
- Nếu bộ E2E cũ flaky nặng mà sửa tốn quá nhiều: **xóa và viết lại** theo chuẩn Playwright (web-first assertion, isolate state) thay vì vá — theo Google, test không đáng tin còn tệ hơn không có test.

---

## 16. Checklist testing strategy

### Trước khi code

- [ ] Đã rõ spec nghiệp vụ (đặc biệt quy tắc tiền/thuế/trạng thái)?
- [ ] Đã xác định test nào cho chức năng này, ở tầng nào (mục 6.4)?
- [ ] Đã có kịch bản edge case: giá trị biên, dữ liệu trùng, quyền thiếu?

### Trong khi code

- [ ] Viết unit test cho logic domain/service (TDD khi logic phức tạp — red → green → refactor)
- [ ] Viết integration/API test cho đường đọc/ghi DB + status/error code
- [ ] Tên test mô tả hành vi + điều kiện
- [ ] Dữ liệu test dùng factory, cô lập, không phụ thuộc thứ tự
- [ ] KHÔNG test implementation detail

### Trước khi merge (PR)

- [ ] `ruff check src tests` + `black --check src tests` + `mypy src` sạch
- [ ] `pytest` xanh toàn bộ (local)
- [ ] Test mới chạy ổn định, không phụ thuộc máy cá nhân
- [ ] Reviewer đã review test (ý nghĩa, đúng tầng, không flaky-prone)
- [ ] PR gate CI xanh (kể cả pip-audit + secret scan)

### Trước khi release

- [ ] E2E critical xanh (hoặc đã cân nhắc cảnh báo nếu đang ở giai đoạn non-gating)
- [ ] Exploratory theo charter đã chạy, không có bug blocker
- [ ] Migration test chạy trên DB sạch + DB có dữ liệu
- [ ] Test chéo DB (nếu production không phải SQLite) đã chạy trong tuần
- [ ] Security mức A xanh; mức B đã rà nếu release lớn
- [ ] Quyết định release có bằng chứng: gate xanh + exploratory + metrics

### Sau khi release

- [ ] Theo dõi bug production tuần đầu; phân loại "bug lọt qua test" → thêm test cho class lỗi đó
- [ ] Ghi nhận flaky mới phát sinh (nếu có) → issue + chủ sở hữu
- [ ] Cập nhật metrics sprint (mục 12)

---

## 17. Anti-patterns cần tránh

| # | Anti-pattern | Vì sao tránh | Thay bằng |
|---|---|---|---|
| 1 | **Test hình thức** (assert trống, test qua loa để "có test") | Tạo cảm giác an toàn giả, tốn thời gian bảo trì | Test assert hành vi quan sát được, có giá trị phát hiện lỗi |
| 2 | **Test quá chậm** (bộ test > 30 phút) | Dev ngừng chạy test, CI tắc | Song song hóa, test nhanh ở tầng thấp, test nặng chuyển staging |
| 3 | **Test quá phụ thuộc UI chi tiết** (CSS class, layout, text chính xác) | Vỡ vụn khi đổi UI, refactor là sửa test | Locator role/label, `data-testid` cho phần phức tạp |
| 4 | **E2E quá nhiều** (test mọi thứ qua UI) | Chậm, flaky, chi phí bảo trì cao — Google/Fowler cảnh báo từ lâu | E2E chỉ critical; đẩy xuống API/unit |
| 5 | **Bỏ qua flaky test** | Giết niềm tin CI; test có thể đang che bug production | Chính sách Sửa/Cách ly/Xóa (mục 11) |
| 6 | **Không có chiến lược test data** (test phụ thuộc data có sẵn, chạy theo thứ tự) | Flaky, kết quả không lặp lại | Factory + cô lập per-test (mục 9) |
| 7 | **Không tích hợp CI** | Test chỉ chạy trên máy dev → vô nghĩa với team | PR gate (mục 8) |
| 8 | **Chỉ QA viết test** | Dev không hiểu test của mình, QA nghẽn cổ chai | Ai cũng viết test, QA giữ hệ thống (mục 13) |
| 9 | **Coverage là mục tiêu duy nhất** | Test viết để "đủ %", không bắt bug | Coverage tham chiếu; gate riêng domain (mục 12) |
| 10 | **Viết test không thể bảo trì** (setup khổng lồ, mock chồng mock, tên vô nghĩa) | Mỗi lần đổi code phải sửa test cả ngày | Test ngắn, độc lập, mô tả hành vi |
| 11 | **Retry để "che" flaky** | Giấu vấn đề, mất dữ liệu chẩn đoán | Retry chỉ chẩn đoán + trace |
| 12 | **Test sau cùng "khi mọi thứ xong"** | Chức năng phức tạp nhất lại ít test nhất, deadline ép bỏ test | Viết test cùng code, từng phần |

---

## 18. Nguồn tham khảo

**Test pyramid / chiến lược tổng thể**

- Google Testing Blog — *Just Say No to More End-to-End Tests* (Mike Wacker, 2015): https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
- Martin Fowler — *Test Pyramid*: https://martinfowler.com/bliki/TestPyramid.html
- Kent C. Dodds — *The Testing Trophy and Testing Classifications*: https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
- Kent C. Dodds — *Write tests. Not too many. Mostly integration.*: https://kentcdodds.com/blog/write-tests
- Google Testing Blog — *Test Flakiness - One of the main challenges of automated testing* (2020/2021, loạt bài): https://testing.googleblog.com/2020/12/test-flakiness-one-of-main-challenges.html

**Flaky test**

- Google Testing Blog — *Flaky Tests at Google and How We Mitigate Them* (John Micco, 2016): https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html
- Google Testing Blog — *Where do our flaky tests come from?* (2017): https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html

**E2E / Playwright**

- Playwright — *Best Practices*: https://playwright.dev/docs/best-practices
- Playwright — *Continuous Integration*: https://playwright.dev/docs/ci
- Playwright — *Test Isolation / Parallelism*: https://playwright.dev/docs/test-parallel

**Security**

- OWASP — *Web Security Testing Guide (WSTG)*, v4.2 stable / v5.0 in development: https://owasp.org/www-project-web-security-testing-guide/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

**Công cụ (tài liệu chính thức)**

- pytest: https://docs.pytest.org/
- SQLAlchemy testing / in-memory SQLite: https://docs.sqlalchemy.org/ (phần "Testing with SQLAlchemy")
- Flask testing: https://flask.palletsprojects.com/ (Testing chapter)
- GitHub Actions: https://docs.github.com/actions

> Ghi chú: đây là các nguồn đã kiểm chứng tại thời điểm viết (2026-08). Nếu cần trích dẫn chi tiết cho từng quyết định, xem link tương ứng. Không dùng nguồn blog cá nhân làm chuẩn khi đã có tài liệu chính thức hoặc thực tiễn phổ biến xác nhận.

---

## Phụ lục A — Quyết định nhanh khi chọn test cho feature mới

```
  Feature mới bắt đầu
      |
      v
  1. Spec đã rõ? ---------- KHÔNG --> Hỏi PO/viết spec trước, đừng test "bừa"
      | CÓ
      v
  2. Có logic thuần? ------ CÓ --> Unit test (parametrize edge case)
      | KHÔNG
      v
  3. Có đọc/ghi DB? ------- CÓ --> Integration test (repo) + API test (endpoint)
      | KHÔNG
      v
  4. Có luồng UI quan trọng? CÓ --> 1 E2E spec (critical journey)
      | KHÔNG
      v
  5. Test tay nhẹ hoặc bỏ qua; ưu tiên thời gian cho bước 2-4
```

---

*Tài liệu này là bản sống (living document) — cập nhật khi team đạt các mốc trong mục 15 hoặc khi thông tin đầu vào thay đổi (thay đổi DB production, thêm SPA, thay CI platform...). Mọi thay đổi lớn nên được review lại với cả team.*
