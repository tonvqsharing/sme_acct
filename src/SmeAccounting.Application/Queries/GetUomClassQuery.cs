using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetUomClassQuery(long Id) : IRequest<UomClassDto?>;

public record GetUomClassesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<UomClassDto>>;