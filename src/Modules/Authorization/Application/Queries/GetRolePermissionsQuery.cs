using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Queries;

public sealed record GetRolePermissionsQuery(string RoleName) : IRequest<Result<IReadOnlyList<string>>>;

public sealed class GetRolePermissionsQueryHandler : IRequestHandler<GetRolePermissionsQuery, Result<IReadOnlyList<string>>>
{
    private readonly IRoleService _roles;

    public GetRolePermissionsQueryHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result<IReadOnlyList<string>>> Handle(GetRolePermissionsQuery request, CancellationToken cancellationToken)
    {
        return _roles.GetRolePermissionsAsync(request.RoleName, cancellationToken);
    }
}
