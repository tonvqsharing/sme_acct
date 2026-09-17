using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxExemptionReasonsByTaxTypeQuery(long TaxTypeId) : IRequest<IReadOnlyList<TaxExemptionReasonDto>>;
