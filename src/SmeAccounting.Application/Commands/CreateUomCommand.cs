using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateUomCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Symbol = null,
    string? Description = null) : IRequest<CreateUomResult>;

public record CreateUomResult(long Id);
