# E-Invoice Integration

## Overview

Mandatory since July 1, 2022 under Decree 123/2020/ND-CP. Amended by Decree 70/2025/ND-CP (June 1, 2025). XML is the legally binding format.

## Decree 123/2020 Requirements

### Two Types of E-Invoices

| Type | Vietnamese | Description | Tax Authority Code | Data Transmission |
|------|-----------|-------------|-------------------|-------------------|
| **With code** | Có mã | Real-time clearance by GDT before issuance | Required — GDT issues authentication code | Real-time via GDT portal or TVAN provider |
| **Without code** | Không có mã | Issued directly, reported same-day | Not required | Data transmitted to GDT no later than issuance day |

### Key Technical Requirements

| Requirement | Detail | Architecture Impact |
|-------------|--------|---------------------|
| **Format** | Standardized XML per GDT specification | `IEInvoiceProvider` interface returns XML; TVAN adapter generates XML |
| **Digital signature** | Mandatory (except POS cash registers); GDT-approved certificate | `IDigitalSignatureService` port interface; adapter for HSM/USB token |
| **Language** | Vietnamese (foreign text in parentheses) | Localization support in invoice generation |
| **Retention** | 10 years in original XML form with digital signature | `EInvoice` entity with `XmlContent`, `DigitalSignature`, `IssuedAt` fields |
| **Archive** | Original electronic form (XML + signature); in-house or outsourced | File storage port interface; blob storage or file system |
| **Data transmission** | XML via secure web services to GDT or TVAN provider | `IEInvoiceProvider.SubmitAsync(EInvoiceRequest)` returns `EInvoiceResponse` |
| **Error handling** | Invalid format: VND 4-8M fine; missing invoice: VND 5-10M fine | Validation before submission; retry logic |

## XML Format Structure

The legally binding format is **XML** (not PDF). PDF is convenience-only.

```
Hóa đơn điện tử (E-Invoice XML)
├── Transaction Data (Thông tin nghiệp vụ)
│   ├── Seller Information (Thông tin người bán)
│   │   ├── Name, Address, Tax Code (MST)
│   │   ├── Bank account info
│   │   └── Digital signature
│   ├── Buyer Information (Thông tin người mua)
│   │   ├── Name, Address, Tax Code (MST)
│   │   └── Representative
│   ├── Invoice Header
│   │   ├── Invoice series (Ký hiệu)
│   │   ├── Invoice number (Số hóa đơn)
│   │   ├── Invoice date (Ngày lập)
│   │   └── Invoice type (Loại hóa đơn)
│   ├── Invoice Lines (Chi tiết hàng hóa/dịch vụ)
│   │   ├── Item name/description
│   │   ├── Unit, Quantity
│   │   ├── Unit price
│   │   ├── Amount (before VAT)
│   │   ├── VAT rate (%)
│   │   ├── VAT amount
│   │   └── Total amount
│   ├── Summary
│   │   ├── Total before VAT
│   │   ├── Total VAT
│   │   ├── Total after VAT
│   │   └── Amount in words (số tiền bằng chữ)
│   └── Additional fields (contract ref, delivery order, etc.)
├── Digital Signature (Chữ ký số)
│   └── GDT-approved certificate (USB token or cloud HSM)
└── Tax Authority Code (Mã cơ quan thuế) — if applicable
    └── Real-time authentication code from GDT
```

## TVAN Provider Adapter Pattern

### Port Interface Design (IEInvoiceProvider)

```csharp
namespace SmeAccounting.Domain.Ports;

public interface IEInvoiceProvider
{
    Task<EInvoiceResponse> SubmitAsync(EInvoiceRequest request, CancellationToken cancellationToken = default);
    Task<EInvoiceStatus> GetStatusAsync(string invoiceId, CancellationToken cancellationToken = default);
}
```

### Request/Response Models

```csharp
public record EInvoiceRequest(
    string InvoiceSeries,
    string InvoiceNumber,
    DateTimeOffset InvoiceDate,
    PartyInfo Seller,
    PartyInfo Buyer,
    IReadOnlyList<InvoiceLine> Lines,
    decimal TotalBeforeVat,
    decimal TotalVat,
    decimal TotalAfterVat,
    string AmountInWords,
    string TemplateCode
);

public record EInvoiceResponse(
    bool Success,
    string? TransactionId,
    string? AuthenticationCode,
    string? XmlContent,
    string? ErrorMessage
);

public record PartyInfo(
    string Name,
    string Address,
    string TaxCode,
    string? BankAccount,
    string? BankName
);

public record InvoiceLine(
    string ItemName,
    string Unit,
    decimal Quantity,
    decimal UnitPrice,
    decimal Amount,
    decimal VatRate,
    decimal VatAmount
);

public record EInvoiceStatus(
    string InvoiceId,
    string Status,
    string? AuthenticationCode,
    DateTimeOffset? ProcessedAt
);
```

### Adapter Implementations

```
IEInvoiceProvider (Domain/Application port)
├── ViettelEInvoiceAdapter (Infrastructure)
├── MisaEInvoiceAdapter (Infrastructure)
├── BkavEInvoiceAdapter (Infrastructure)
├── VnptEInvoiceAdapter (Infrastructure)
├── FptEInvoiceAdapter (Infrastructure)
└── MInvoiceAdapter (Infrastructure)
```

### TVAN Providers

| Provider | Market Share | API Style | Notes |
|----------|-------------|-----------|-------|
| **Viettel** | ~40% market | REST API | Largest telecom; integrated e-invoice platform |
| **MISA** | ~25% market | REST API | Accounting software + e-invoice bundle |
| **BKAV** | ~10% market | REST API | Digital signature + e-invoice |
| **VNPT** | ~10% market | REST API | State telecom |
| **FPT** | ~8% market | REST API | Tech conglomerate |
| **M-Invoice** | ~5% market | REST API | Specialized e-invoice provider |

## Digital Signature Port Interface

```csharp
namespace SmeAccounting.Domain.Ports;

public interface IDigitalSignatureService
{
    Task<byte[]> SignAsync(byte[] data, CancellationToken cancellationToken = default);
    Task<bool> VerifyAsync(byte[] data, byte[] signature, CancellationToken cancellationToken = default);
}
```

## Decree 70/2025 Updates

- Expanded scope to overseas suppliers without PE in Vietnam (voluntary e-invoice registration)
- Stricter retail/POS rules
- Real-time data transmission and regulatory reporting for consumer-facing businesses
- Integrated e-invoice + e-receipt format allowed for single-transaction payments

## Registration

Enterprises register via GDT e-portal (Form 01/DKTD-HDDT) or through TVAN providers.

## Traceability Matrix

| Regulation | Article/Section | Architecture Component | Layer | Test | Status |
|-----------|-----------------|----------------------|-------|------|--------|
| Decree 123 | Art. 12 | EInvoice XML generation | Infrastructure | EInvoiceAdapterTests | Planned |
| Decree 123 | Art. 12 | IEInvoiceProvider | Infrastructure | EInvoiceAdapterTests | Planned |
| Decree 123 | Art. 12 | IDigitalSignatureService | Infrastructure | DigitalSignatureTests | Planned |
| Decree 70 | Art. 1 | TVAN adapter pattern | Infrastructure | EInvoiceAdapterTests | Planned |
| Circular 99 | Art. 28(dd) | Port/adapter interfaces | Infrastructure | ArchitectureTests | Planned |
