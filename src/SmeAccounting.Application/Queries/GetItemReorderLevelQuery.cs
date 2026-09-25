using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemReorderLevelQuery(long Id) : IRequest<ItemReorderLevelDto?>;

public record GetItemReorderLevelsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemReorderLevelDto>>;
