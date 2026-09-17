using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxRateQuery(long TaxRateId) : IRequest<TaxRateDto?>;
