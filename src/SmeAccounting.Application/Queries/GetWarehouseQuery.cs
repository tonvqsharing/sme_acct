using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetWarehouseQuery(long Id) : IRequest<WarehouseDto?>;

public record GetWarehousesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<WarehouseDto>>;
