using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record RevokePermissionFromRoleCommand(string RoleName, string Permission) : IRequest<Result>;

public sealed class RevokePermissionFromRoleCommandHandler : IRequestHandler<RevokePermissionFromRoleCommand, Result>
{
    private readonly IRoleService _roles;

    public RevokePermissionFromRoleCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(RevokePermissionFromRoleCommand request, CancellationToken cancellationToken)
    {
        return _roles.RevokePermissionAsync(request.RoleName, request.Permission, cancellationToken);
    }
}
