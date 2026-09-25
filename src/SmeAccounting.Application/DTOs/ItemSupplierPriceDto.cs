namespace SmeAccounting.Application.DTOs;

public record ItemSupplierPriceDto(
    long Id,
    long CompanyId,
    long SupplierId,
    long ItemId,
    decimal UnitPrice,
    string CurrencyCode,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo,
    bool IsActive);
