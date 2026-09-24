using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemPriceListQuery(long Id) : IRequest<ItemPriceListDto?>;

public record GetItemPriceListsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemPriceListDto>>;