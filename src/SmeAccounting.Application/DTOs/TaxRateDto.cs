namespace SmeAccounting.Application.DTOs;

public record TaxRateDto(
    long Id,
    long CompanyId,
    long TaxTypeId,
    decimal RateValue,
    string RateName,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo,
    bool IsActive,
    string? Description);
