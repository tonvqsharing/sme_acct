using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxTreatmentsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<TaxTreatmentDto>>;
