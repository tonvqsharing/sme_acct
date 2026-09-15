using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record DeleteRoleCommand(string RoleName) : IRequest<Result>;

public sealed class DeleteRoleCommandHandler : IRequestHandler<DeleteRoleCommand, Result>
{
    private readonly IRoleService _roles;

    public DeleteRoleCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(DeleteRoleCommand request, CancellationToken cancellationToken)
    {
        return _roles.DeleteAsync(request.RoleName, cancellationToken);
    }
}
