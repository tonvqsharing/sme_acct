using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxExemptionReasonsByTaxTypeHandler(
    ITaxExemptionReasonRepository repository)
    : IRequestHandler<GetTaxExemptionReasonsByTaxTypeQuery, IReadOnlyList<TaxExemptionReasonDto>>
{
    public async Task<IReadOnlyList<TaxExemptionReasonDto>> Handle(
        GetTaxExemptionReasonsByTaxTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByTaxTypeAsync(request.TaxTypeId);
        return entities
            .Select(e => new TaxExemptionReasonDto(
                e.Id, e.CompanyId, e.TaxTypeId,
                e.Code, e.Name, e.LegalBasis,
                e.Description, e.IsActive))
            .ToList();
    }
}
