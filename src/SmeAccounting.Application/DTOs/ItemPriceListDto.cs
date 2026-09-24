namespace SmeAccounting.Application.DTOs;

public record ItemPriceListDto(
    long Id,
    long CompanyId,
    long PriceListId,
    long ItemId,
    decimal UnitPrice,
    string CurrencyCode,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo,
    bool IsActive);