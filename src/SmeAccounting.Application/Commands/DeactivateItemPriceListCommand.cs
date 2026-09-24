using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemPriceListCommand(long Id) : IRequest<DeactivateItemPriceListResult>;

public record DeactivateItemPriceListResult(bool Success);