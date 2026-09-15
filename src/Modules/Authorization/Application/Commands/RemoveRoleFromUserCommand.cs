using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record RemoveRoleFromUserCommand(Guid UserId, string RoleName) : IRequest<Result>;

public sealed class RemoveRoleFromUserCommandHandler : IRequestHandler<RemoveRoleFromUserCommand, Result>
{
    private readonly IRoleService _roles;

    public RemoveRoleFromUserCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(RemoveRoleFromUserCommand request, CancellationToken cancellationToken)
    {
        return _roles.RemoveRoleFromUserAsync(request.UserId, request.RoleName, cancellationToken);
    }
}
