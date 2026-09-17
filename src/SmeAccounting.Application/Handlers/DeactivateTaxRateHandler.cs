using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxRateHandler(
    ITaxRateRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxRateCommand, DeactivateTaxRateResult>
{
    public async Task<DeactivateTaxRateResult> Handle(
        DeactivateTaxRateCommand request,
        CancellationToken cancellationToken)
    {
        var taxRate = await repository.GetByIdAsync(request.TaxRateId);
        if (taxRate is null)
            throw new InvalidOperationException($"Tax rate with ID {request.TaxRateId} not found.");

        taxRate.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxRateResult();
    }
}
