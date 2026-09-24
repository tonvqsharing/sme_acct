using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetPriceListQuery(long Id) : IRequest<PriceListDto?>;

public record GetPriceListsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<PriceListDto>>;