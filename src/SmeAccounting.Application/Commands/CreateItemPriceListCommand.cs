using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemPriceListCommand(
    long CompanyId,
    long PriceListId,
    long ItemId,
    decimal UnitPrice,
    string CurrencyCode,
    DateOnly EffectiveFrom,
    DateOnly? EffectiveTo = null) : IRequest<CreateItemPriceListResult>;

public record CreateItemPriceListResult(long Id);