using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetTaxTreatmentsByTaxTypeQuery(long TaxTypeId) : IRequest<IReadOnlyList<TaxTreatmentDto>>;
