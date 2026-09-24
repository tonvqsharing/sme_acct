using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivatePriceListCommand(long Id) : IRequest<DeactivatePriceListResult>;

public record DeactivatePriceListResult(bool Success);