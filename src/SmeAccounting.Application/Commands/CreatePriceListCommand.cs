using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreatePriceListCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreatePriceListResult>;

public record CreatePriceListResult(long Id);