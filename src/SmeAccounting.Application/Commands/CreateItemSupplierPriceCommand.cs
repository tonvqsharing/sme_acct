using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemSupplierPriceCommand(
    long CompanyId,
    long SupplierId,
    long ItemId,
    decimal UnitPrice,
    string CurrencyCode,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo = null) : IRequest<CreateItemSupplierPriceResult>;

public record CreateItemSupplierPriceResult(long Id);
