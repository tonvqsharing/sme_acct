using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemQuery(long Id) : IRequest<ItemDto?>;

public record GetItemsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemDto>>;
