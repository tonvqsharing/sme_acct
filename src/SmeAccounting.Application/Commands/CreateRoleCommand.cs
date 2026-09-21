using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateRoleCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Description = null) : IRequest<CreateRoleResult>;

public record CreateRoleResult(long Id);
