using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record AssignRoleToUserCommand(Guid UserId, string RoleName) : IRequest<Result>;

public sealed class AssignRoleToUserCommandHandler : IRequestHandler<AssignRoleToUserCommand, Result>
{
    private readonly IRoleService _roles;

    public AssignRoleToUserCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(AssignRoleToUserCommand request, CancellationToken cancellationToken)
    {
        return _roles.AssignRoleToUserAsync(request.UserId, request.RoleName, cancellationToken);
    }
}
