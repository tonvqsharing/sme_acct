using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Commands;

public sealed record CreateRoleCommand(string RoleName, string? Description) : IRequest<Result>;

public sealed class CreateRoleCommandHandler : IRequestHandler<CreateRoleCommand, Result>
{
    private readonly IRoleService _roles;

    public CreateRoleCommandHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result> Handle(CreateRoleCommand request, CancellationToken cancellationToken)
    {
        return _roles.CreateAsync(request.RoleName, request.Description, cancellationToken);
    }
}
