using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxRuleHandler(
    ITaxRuleRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxRuleCommand, DeactivateTaxRuleResult>
{
    public async Task<DeactivateTaxRuleResult> Handle(
        DeactivateTaxRuleCommand request,
        CancellationToken cancellationToken)
    {
        var taxRule = await repository.GetByIdAsync(request.TaxRuleId);
        if (taxRule is null)
            throw new InvalidOperationException($"Tax rule with ID {request.TaxRuleId} not found.");

        taxRule.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxRuleResult();
    }
}
