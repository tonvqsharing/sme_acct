using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxTreatmentsByCompanyHandler(
    ITaxTreatmentRepository repository)
    : IRequestHandler<GetTaxTreatmentsByCompanyQuery, IReadOnlyList<TaxTreatmentDto>>
{
    public async Task<IReadOnlyList<TaxTreatmentDto>> Handle(
        GetTaxTreatmentsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxTreatmentDto(
                e.Id, e.Code, e.Name,
                e.TaxTypeId, e.TaxTreatmentType.ToString(),
                e.InputCreditAllowed, e.CompanyId,
                e.IsActive, e.Description))
            .ToList();
    }
}
