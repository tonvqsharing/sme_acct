namespace SmeAccounting.Application.DTOs;

public record TaxTreatmentDto(
    long Id,
    string Code,
    string Name,
    long TaxTypeId,
    string TaxTreatmentType,
    bool InputCreditAllowed,
    long CompanyId,
    bool IsActive,
    string? Description);
