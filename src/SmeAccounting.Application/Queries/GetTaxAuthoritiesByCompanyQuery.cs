using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxAuthoritiesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxAuthorityDto>>;
