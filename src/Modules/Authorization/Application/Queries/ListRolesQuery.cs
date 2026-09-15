using MediatR;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Modules.Authorization.Application.Queries;

public sealed record ListRolesQuery : IRequest<Result<IReadOnlyList<string>>>;

public sealed class ListRolesQueryHandler : IRequestHandler<ListRolesQuery, Result<IReadOnlyList<string>>>
{
    private readonly IRoleService _roles;

    public ListRolesQueryHandler(IRoleService roles)
    {
        _roles = roles;
    }

    public Task<Result<IReadOnlyList<string>>> Handle(ListRolesQuery request, CancellationToken cancellationToken)
    {
        return _roles.ListRolesAsync(cancellationToken);
    }
}
