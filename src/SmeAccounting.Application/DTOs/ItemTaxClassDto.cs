namespace SmeAccounting.Application.DTOs;

public record ItemTaxClassDto(
    long Id,
    long CompanyId,
    long ItemId,
    long TaxTypeId,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo,
    bool IsActive);