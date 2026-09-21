using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetRolesByCompanyHandler(IRoleRepository repository)
    : IRequestHandler<GetRolesByCompanyQuery, IReadOnlyList<RoleDto>>
{
    public async Task<IReadOnlyList<RoleDto>> Handle(GetRolesByCompanyQuery request, CancellationToken cancellationToken)
    {
        var roles = await repository.GetAllByCompanyAsync(request.CompanyId);
        return roles.Select(r => new RoleDto(r.Id, r.CompanyId, r.Code, r.Name, r.Description, r.IsActive)).ToList();
    }
}
