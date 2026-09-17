namespace SmeAccounting.Application.DTOs;

public record TaxRuleDto(
    long Id,
    long CompanyId,
    long TaxTypeId,
    long? TaxRateId,
    long TaxTreatmentId,
    string Code,
    string Name,
    string? Conditions,
    string LegalReference,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo,
    bool IsActive,
    string? Description);
