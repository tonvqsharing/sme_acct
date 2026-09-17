using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxExemptionReasonsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxExemptionReasonDto>>;
