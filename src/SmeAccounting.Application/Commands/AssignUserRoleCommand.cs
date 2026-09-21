using MediatR;

namespace SmeAccounting.Application.Commands;

public record AssignUserRoleCommand(
    long UserId,
    long RoleId,
    long CompanyId) : IRequest<AssignUserRoleResult>;

public record AssignUserRoleResult(long Id);
