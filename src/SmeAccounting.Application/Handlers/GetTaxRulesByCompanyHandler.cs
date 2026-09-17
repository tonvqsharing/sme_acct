using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxRulesByCompanyHandler(
    ITaxRuleRepository repository)
    : IRequestHandler<GetTaxRulesByCompanyQuery, IReadOnlyList<TaxRuleDto>>
{
    public async Task<IReadOnlyList<TaxRuleDto>> Handle(
        GetTaxRulesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxRuleDto(
                e.Id, e.CompanyId, e.TaxTypeId,
                e.TaxRateId, e.TaxTreatmentId,
                e.Code, e.Name, e.Conditions,
                e.LegalReference, e.EffectiveFrom,
                e.EffectiveTo, e.IsActive, e.Description))
            .ToList();
    }
}
