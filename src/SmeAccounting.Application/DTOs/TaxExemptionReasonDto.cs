namespace SmeAccounting.Application.DTOs;

public record TaxExemptionReasonDto(
    long Id,
    long CompanyId,
    long TaxTypeId,
    string Code,
    string Name,
    string LegalBasis,
    string? Description,
    bool IsActive);
