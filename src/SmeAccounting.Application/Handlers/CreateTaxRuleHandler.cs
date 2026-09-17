using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTaxRuleHandler(
    ITaxRuleRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTaxRuleCommand, CreateTaxRuleResult>
{
    public async Task<CreateTaxRuleResult> Handle(
        CreateTaxRuleCommand request,
        CancellationToken cancellationToken)
    {
        var taxRule = new TaxRule(
            request.CompanyId, request.TaxTypeId,
            request.TaxRateId, request.TaxTreatmentId,
            request.Code, request.Name, request.LegalReference,
            request.EffectiveFrom, request.EffectiveTo,
            request.Conditions, request.Description);

        await repository.AddAsync(taxRule);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTaxRuleResult(taxRule.Id);
    }
}
