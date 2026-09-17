using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetOpeningBalanceMappingsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<OpeningBalanceMappingDto>>;
