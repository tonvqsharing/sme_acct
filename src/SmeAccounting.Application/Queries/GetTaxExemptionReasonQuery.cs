using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxExemptionReasonQuery(long TaxExemptionReasonId) : IRequest<TaxExemptionReasonDto?>;
