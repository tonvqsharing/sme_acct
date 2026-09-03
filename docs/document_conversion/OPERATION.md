# Operation Guide — Document Conversion (MarkItDown) — sme_acct

**Brick:** `src/bricks/document_conversion` | **Package:** `markitdown[all] 0.1.7` (Microsoft) | **Status:** ✅ PROD wired `2026-09-03` | **Tests:** 14 (11 unit + 3 integration) | **Gate:** `ruff/black/mypy 109 Success` + `pytest 968` (954→968)

---

## 1. Why MarkItDown in sme_acct?

- Convert **invoices, contracts, bank statements, financial statements** from `PDF/DOCX/XLSX/HTML/CSV` → **Markdown** for LLM pipelines (audit, auto-journal, tax cate).
- Preserves **structure**: headings, lists, tables, links → token-efficient for GPT-4o/MISA AI.
- Replaces `textract` style dump; used **offline** (no Azure cost) unless `llm_client`/`cu_endpoint` explicitly enabled.

**Vietnamese SME flows where it helps:**
- Supplier sends `Hóa đơn PDF` → `POST /documents/convert` → Markdown → feed `PurchaseService` deductibility + `XML ingest` (if TT91 XML inside PDF).
- Bank sends `Sao kê XLSX` → Markdown table → `ReconciliationService`
- `BCTC PDF` from MISA/FAST → Markdown → `ReportEngine` compare

---

## 2. Installation (already done via `uv`)

```bash
# Already pinned in pyproject.toml
uv add "markitdown[all]>=0.1.7"
# Verify
uv run python -c "from markitdown import MarkItDown; print(MarkItDown().convert_stream)"
```

**What `uv add` pulled:** `pdfminer-six`, `pdfplumber`, `python-pptx`, `openpyxl`, `pandas`, `pillow`, `speechrecognition`, `youtube-transcript-api`, etc. Full list `uv pip list | grep -E "pdf|pptx|openpyxl|pillow"`.

**No `ffmpeg` needed** for office docs; warning `Couldn't find ffmpeg` is harmless (only for `wav/mp3` audio).

---

## 3. How to Use in Operation

### 3.1 REST API (recommended for SME operators — no code)

**Base:** `POST /api/v1/documents/*` — all `@login_required`, any authenticated role can convert; `AUDITOR` read-only still can convert (read operation), no `AUDITOR` block on this brick (intentional).

#### A. Single file → Markdown

```bash
# Login first (session cookie)
curl -c cookie.txt -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"..."}'

# Convert one PDF/DOCX/XLSX
curl -b cookie.txt -X POST http://localhost:5000/api/v1/documents/convert \
  -F "file=@/path/to/HoaDon_NCC_A.pdf" | jq .

# Raw body alternative (filename via query)
curl -b cookie.txt -X POST "http://localhost:5000/api/v1/documents/convert?file_name=report.xlsx" \
  --data-binary @report.xlsx -H "Content-Type: application/octet-stream" | jq .
```

**Response 200:**

```json
{
  "data": {
    "file_name": "HoaDon_NCC_A.pdf",
    "file_type": "pdf",
    "title": "Hóa đơn GTGT",
    "markdown": "# Hóa đơn\n| Mã | Tên | SL | Đơn giá |\n|---|---|---|---|\n...",
    "warnings": ["Đã cắt 520000 → 500000 chars"] // only if >500k
  }
}
```

**Error 422:**

```json
{"error":"Định dạng .exe chưa hỗ trợ (chỉ: ['bmp','csv',...])","code":"INVALID_FILE"}
{"error":"File quá lớn (25000000 bytes > 20971520)","code":"INVALID_FILE"}
{"error":"Conversion failed: ...","code":"CONVERSION_FAILED"}
```

#### B. Batch (≤10 files)

```bash
curl -b cookie.txt -X POST http://localhost:5000/api/v1/documents/convert-batch \
  -F "files=@/a.pdf" -F "files=@/b.docx" -F "files=@/c.xlsx" | jq .
```

Response `200` with `data: [{file_name, file_type, success, markdown, error, warnings}, ...]` — partial success allowed (one bad file doesn't fail whole batch).

#### C. Supported types

```bash
curl -b cookie.txt http://localhost:5000/api/v1/documents/supported-types | jq .
# {"data": {"extensions": ["bmp","csv","doc","docx",...,"zip"], "max_bytes": 20971520}}
```

**Limits enforced in `domain.py`:**
- `MAX_BYTES = 20 MB` per file
- `MAX_MARKDOWN_CHARS = 500_000` (auto-truncated with warning)
- `ALLOWED_EXTENSIONS` 24 types; `../`/`/`,`\` traversal blocked → `422 Tên file không hợp lệ`

### 3.2 Python Service (for brick-to-brick automation)

```python
from src.bricks.document_conversion.services import DocumentConversionService

svc = DocumentConversionService()  # enable_plugins=False default (offline, safe)
# Optional LLM for image OCR / YouTube:
# svc = DocumentConversionService(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")

# Bytes → Markdown
with open("HoaDon.pdf", "rb") as f:
    data = f.read()
res = svc.convert_bytes(data=data, file_name="HoaDon.pdf")
if res.success:
    print(res.markdown)  # feed to PurchaseService or LLM
else:
    print(res.error)

# Stream → Markdown (narrowest API per Security Considerations)
import io
res2 = svc.convert_stream(io.BytesIO(b"a,b\n1,2"), file_name="data.csv")
```

**Bridge to Purchases (example):**

```python
# After MarkItDown → parse Markdown table for supplier invoice
from src.bricks.purchases.services import PurchaseService
# ... svc.convert_bytes -> res.markdown contains "| Mã | Tên | SL | Giá |" 
# Parse with simple regex, then:
purchase_svc.create_invoice(
    company_id=cid, supplier_name="NCC A", supplier_mst="0123456789",
    invoice_number="0001234", invoice_symbol="C25TAA",
    invoice_date=date(2026,9,3), entry_date=date(2026,9,3),
    lines=[{"expense_account":"6421","amount_pre_vat":"10000000","vat_rate":"0.1"}],
    actor=actor, reason="markitdown: HoaDon.pdf"
)
```

### 3.3 CLI (dev/debug, not PROD)

```bash
uv run markitdown path-to-file.pdf > document.md
uv run markitdown path-to-file.pdf -o document.md
cat file.pdf | uv run markitdown
# With LLM image description (needs OPENAI_API_KEY):
uv run python -c "from markitdown import MarkItDown; from openai import OpenAI; md=MarkItDown(llm_client=OpenAI(), llm_model='gpt-4o'); print(md.convert('scan.jpg').text_content)"
```

### 3.4 Chained Flow: MarkItDown → LLM → Accounting (recommended)

```
Supplier PDF (mail/portal)
  → POST /documents/convert → Markdown (structure preserved)
  → LLM (MISA AI / GPT-4o) prompt: "Extract {supplier_mst, invoice_number, lines:{account, amount, vat_rate}} as JSON"
  → POST /purchase-invoices (with actor/reason audit)
  → POST /purchase-invoices/<id>/post → ledger → VAT declaration 01/GTGT
  → GET /documents/supported-types (pre-check) + validation
```

---

## 4. Security — MUST READ (per upstream Security Considerations)

MarkItDown does I/O with current process privileges. **Sanitize inputs:**

- **Only call `convert_stream` / `convert_bytes`** (narrowest). Brick does this — never uses `convert()` which fetches remote URIs.
- **Validate file_name** via `validate_file_name()` — blocks `../`, `/`, `\`, and disallows `.exe/.sh` etc. Only `ALLOWED_EXTENSIONS`.
- **Enforce size** `MAX_BYTES 20 MB` at domain boundary before `MarkItDown` — prevents token blow-up / DoS.
- **No URL fetch:** If you need YouTube, fetch `requests.get` yourself, validate scheme `https` only, then `convert_stream`.
- **Run offline by default:** `enable_plugins=False` — plugins disabled unless `MARKITDOWN_ENABLE_PLUGINS=1` + explicit `llm_client`.

---

## 5. Configuration

**No env vars required for offline office docs.** Optional:

```bash
# Enable LLM Vision for image OCR (embedded images in PDF/DOCX)
export OPENAI_API_KEY="sk-..."
# In code: DocumentConversionService(enable_plugins=True, llm_client=OpenAI(), llm_model="gpt-4o")

# Azure Document Intelligence (higher quality, billable)
export MARKITDOWN_DOCINTEL_ENDPOINT="https://<resource>.cognitiveservices.azure.com/"
# Then: MarkItDown(docintel_endpoint=os.environ["MARKITDOWN_DOCINTEL_ENDPOINT"])

# Azure Content Understanding (structured fields → YAML front matter, video)
export MARKITDOWN_CU_ENDPOINT="https://<cu>.cognitiveservices.azure.com/"
```

**FFmpeg (audio only):** `apt install ffmpeg` if you need `mp3/wav` transcription; otherwise ignore warning.

---

## 6. Operation Runbook (SME Accountant)

**Daily:**
1. Receive supplier `PDF HOA DON` via email → download to `Inbox/`
2. Upload via `POST /documents/convert` (single) → copy Markdown → paste to LLM prompt → verify extracted `MST, số hóa đơn, tiền trước thuế, thuế suất`
3. Create purchase invoice via UI (or script) → system auto checks `FY period open → COA posting → catalog 0/5/8/10 → 8% category gate → duplicate guard`
4. If `PENDING_PROOF` (≥5tr without non-cash proof) → `POST /purchase-invoices/<id>/proof` after uploading bank proof

**Monthly:**
- `GET /reports/vat-declaration?month=8&format=gdt_xml` → upload `thuedientu.gdt.gov.vn`
- For `BCTC` PDF from MISA → `POST /documents/convert-batch` → Markdown → feed to `ReportEngine` compare

**Troubleshooting:**

| Symptom | Cause | Fix |
|---|---|---|
| `422 INVALID_FILE .exe` | Disallowed extension | Rename to `.pdf/.docx` or add to `ALLOWED_EXTENSIONS` if needed (requires dev) |
| `422 File quá lớn` | >20 MB | Split ZIP or compress PDF; raise `MAX_BYTES` in `domain.py` if policy allows (requires Chief Accountant approval) |
| `CONVERSION_FAILED` | Corrupt PDF / password-protected | Open in Adobe, re-save without password, retry |
| `Couldn't find ffmpeg` warning | Audio `mp3/wav` without ffmpeg | `apt install ffmpeg` or ignore if only office docs |
| Empty markdown | Scanned PDF without OCR | Enable LLM Vision: `DocumentConversionService(enable_plugins=True, llm_client=OpenAI())` + `pip install markitdown-ocr` |

---

## 7. Integration Points in sme_acct

- **Brick:** `src/bricks/document_conversion/{contract,domain,services,storage,web_adapter}.py` — Lego 5-file, `web_adapter` only Flask
- **Wired in:** `src/app.py:193` init `DocumentConversionService()` + `document_conversion_bp` (17th blueprint) + `DocConvBase.metadata.create_all`
- **Alembic:** `DocConvBase` stateless → no migration needed (no tables)
- **Tests:** `tests/unit/document_conversion/` (domain+service) + `tests/integration/test_document_conversion_api.py` (3) — total 968 (954→968)
- **Mypy:** `markitdown.*` + `numpy.*` `ignore_errors=true`, `python_version=3.13` (type statement in numpy stub)
- **Next:** Wire MarkItDown → `PurchaseService` auto-fill in UI (`HTMX` upload field `hx-post="/api/v1/documents/convert"` → preview Markdown → confirm → create invoice)

---

## 8. References

- Upstream: `https://github.com/microsoft/markitdown` (MIT, 177k stars, 381 issues, `packages/markitdown` + `markitdown-sample-plugin` + `markitdown-ocr`)
- Installed: `markitdown[all] 0.1.7` via `uv add` — see `pyproject.toml` `dependencies` + `uv.lock`
- SME verification: `uv run python -c "from markitdown import MarkItDown; print(MarkItDown().convert_stream)"` OK

> **Chief Accountant note:** MarkItDown does **not** validate Vietnamese tax law. Always re-validate extracted `vat_rate` via `rate_gate` (8% window + category) before posting. Markdown is for **LLM consumption**, not human fidelity rendering.
