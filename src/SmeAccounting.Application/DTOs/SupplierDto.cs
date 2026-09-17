namespace SmeAccounting.Application.DTOs;

public record SupplierDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string? TaxCode,
    string? Address,
    string? Phone,
    string? Email,
    long? PaymentTermId,
    long? DefaultTaxTypeId,
    bool IsActive,
    string? Description);
