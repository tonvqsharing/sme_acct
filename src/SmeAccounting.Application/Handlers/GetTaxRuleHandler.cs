using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxRuleHandler(
    ITaxRuleRepository repository)
    : IRequestHandler<GetTaxRuleQuery, TaxRuleDto?>
{
    public async Task<TaxRuleDto?> Handle(
        GetTaxRuleQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxRuleId);
        return entity is null ? null : new TaxRuleDto(
            entity.Id, entity.CompanyId, entity.TaxTypeId,
            entity.TaxRateId, entity.TaxTreatmentId,
            entity.Code, entity.Name, entity.Conditions,
            entity.LegalReference, entity.EffectiveFrom,
            entity.EffectiveTo, entity.IsActive, entity.Description);
    }
}
