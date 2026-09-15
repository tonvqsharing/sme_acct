using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Queries;

public sealed record GetUserPermissionsQuery(Guid UserId) : IRequest<Result<IReadOnlyList<string>>>;

public sealed class GetUserPermissionsQueryHandler : IRequestHandler<GetUserPermissionsQuery, Result<IReadOnlyList<string>>>
{
    private readonly IPermissionService _permissions;

    public GetUserPermissionsQueryHandler(IPermissionService permissions)
    {
        _permissions = permissions;
    }

    public async Task<Result<IReadOnlyList<string>>> Handle(GetUserPermissionsQuery request, CancellationToken cancellationToken)
    {
        var permissions = await _permissions.GetPermissionsAsync(request.UserId, cancellationToken).ConfigureAwait(false);
        return Result<IReadOnlyList<string>>.Create(permissions);
    }
}
