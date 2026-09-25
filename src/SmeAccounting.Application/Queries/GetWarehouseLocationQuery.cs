using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetWarehouseLocationQuery(long Id) : IRequest<WarehouseLocationDto?>;

public record GetWarehouseLocationsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<WarehouseLocationDto>>;