using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetItemSupplierPriceQuery(long Id) : IRequest<ItemSupplierPriceDto?>;

public record GetItemSupplierPricesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<ItemSupplierPriceDto>>;
