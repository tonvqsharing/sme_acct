using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxRatesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxRateDto>>;
