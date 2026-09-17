using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxPeriodQuery(long TaxPeriodId) : IRequest<TaxPeriodDto?>;
