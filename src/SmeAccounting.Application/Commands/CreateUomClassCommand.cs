using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateUomClassCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreateUomClassResult>;

public record CreateUomClassResult(long Id);