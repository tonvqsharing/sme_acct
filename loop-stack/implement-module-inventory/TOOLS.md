# Discovered Tools

REUSED FROM GLOBAL + researcher additions (global file 2026-09-23, <7 days old; verified current by environment researcher 2026-09-24)

## Newly Discovered Resources (Online — Unconfirmed Local)

(researcher-only section — resources found online, NOT confirmed installed/available in this environment; may need setup before use)

| Resource | Type | Use for this loop | Source |
|----------|------|-------------------|--------|
| GS1 General Specifications §7.10 (Check Digit Calculations) | Public standard doc | GTIN check-digit algorithm reference (Mod-10, weights 3/1) | ref.gs1.org/standards/genspecs/10.0.0 |
| GS1 US "How to Calculate a Check Digit" | Official PDF guide | Worked GTIN-12 example of Mod-10 check digit | documents.gs1us.org (GSUS131A_D02) |
| GS1 check digit calculator | Web service | Verify test vectors for GTIN-8/12/13/14 | gs1.org/services/check-digit-calculator |
| VAS 02 English translation (Decision 149/2001/QD-BTC) | Regulatory text | Para 13 valuation methods (specific id, weighted avg, FIFO, LIFO); para 4 NRV; para 11 excluded costs | atax.vn/vas-no-2; jungil.vn/en/standard-no-2-inventories-15.html |
| Circular 200/2014/TT-BTC + 133/2016/TT-BTC valuation methods | Regulatory commentary | Confirms operative VN regime = 3 methods (weighted avg, specific id, FIFO) — NO LIFO | ketoanthienung.vn/cac-phuong-phap-tinh-gia-xuat-kho-cua-hang-ton-kho.htm |
| Circular 99/2025/TT-BTC Art. 31 | Regulatory text | Circular 200 expires 2026-01-01; Circular 108/2026/TT-BTC referenced from 2026-07-24 | luatvietnam.vn/doanh-nghiep/toan-van-thong-tu-200-2014-tt-btc-92289-d1.html |

## Confirmed Local Tools (from global TOOLS.md + this research)

- **codebase-memory-mcp** — CONFIRMED configured; use `search_graph`/`trace_path`/`get_code_snippet` for code discovery (preferred over grep).
- **codegraph** — configured but NO `.codegraph/` index at repo root; DO NOT use (grep/glob/read instead).
- **playwright** — configured; UI testing only (not needed for backend master-data module).
- **headroom** — configured; context compression.
- NuGet landscape: Domain zero-NuGet (arch-enforced); Application MediatR 14.2.0 + FluentValidation 12.1.0; Infrastructure EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions 10.0.*; Api Swashbuckle 10.2.3. No new packages needed for inventory master data.
- EF conventions: snake_case (EFCore.NamingConventions), xmin row version on all tables, enums as string via HasConversion<string>(), FK Restrict to Company, composite unique (CompanyId,Code), decimal via HasPrecision (precedent: UomConversion Factor decimal(18,6)).
