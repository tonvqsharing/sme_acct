using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxPeriodHandler(
    ITaxPeriodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxPeriodCommand, DeactivateTaxPeriodResult>
{
    public async Task<DeactivateTaxPeriodResult> Handle(
        DeactivateTaxPeriodCommand request,
        CancellationToken cancellationToken)
    {
        var taxPeriod = await repository.GetByIdAsync(request.TaxPeriodId);
        if (taxPeriod is null)
            throw new InvalidOperationException($"Tax period with ID {request.TaxPeriodId} not found.");

        taxPeriod.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxPeriodResult();
    }
}
