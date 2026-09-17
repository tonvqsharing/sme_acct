using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxTreatmentsByTaxTypeHandler(
    ITaxTreatmentRepository repository)
    : IRequestHandler<GetTaxTreatmentsByTaxTypeQuery, IReadOnlyList<TaxTreatmentDto>>
{
    public async Task<IReadOnlyList<TaxTreatmentDto>> Handle(
        GetTaxTreatmentsByTaxTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByTaxTypeAsync(request.TaxTypeId);
        return entities
            .Select(e => new TaxTreatmentDto(
                e.Id, e.Code, e.Name,
                e.TaxTypeId, e.TaxTreatmentType.ToString(),
                e.InputCreditAllowed, e.CompanyId,
                e.IsActive, e.Description))
            .ToList();
    }
}
