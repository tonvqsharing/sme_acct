using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetUomQuery(long Id) : IRequest<UomDto?>;

public record GetUomsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<UomDto>>;
