using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxAccountingMappingQuery(long TaxAccountingMappingId) : IRequest<TaxAccountingMappingDto?>;
