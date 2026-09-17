using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxTypesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxTypeDto>>;
