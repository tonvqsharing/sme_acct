using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetRolesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<RoleDto>>;
