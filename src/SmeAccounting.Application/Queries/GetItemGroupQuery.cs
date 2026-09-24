using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemGroupQuery(long Id) : IRequest<ItemGroupDto?>;

public record GetItemGroupsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemGroupDto>>;