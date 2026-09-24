using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemGroupCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreateItemGroupResult>;

public record CreateItemGroupResult(long Id);