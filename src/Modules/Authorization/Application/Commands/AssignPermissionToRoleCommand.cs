using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record AssignPermissionToRoleCommand(string RoleName, string Permission) : IRequest<Result>;

public sealed class AssignPermissionToRoleCommandHandler : IRequestHandler<AssignPermissionToRoleCommand, Result>
{
    private readonly IRoleService _roles;

    public AssignPermissionToRoleCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(AssignPermissionToRoleCommand request, CancellationToken cancellationToken)
    {
        return _roles.AssignPermissionAsync(request.RoleName, request.Permission, cancellationToken);
    }
}
