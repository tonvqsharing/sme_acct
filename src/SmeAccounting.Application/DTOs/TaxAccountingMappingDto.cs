namespace SmeAccounting.Application.DTOs;

public record TaxAccountingMappingDto(
    long Id,
    long CompanyId,
    long TaxTypeId,
    long TaxTreatmentId,
    long AccountId,
    string MappingType,
    bool IsActive,
    string? Description);
