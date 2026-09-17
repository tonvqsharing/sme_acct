using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxAccountingMappingsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxAccountingMappingDto>>;
