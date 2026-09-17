using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTaxAuthorityHandler(
    ITaxAuthorityRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTaxAuthorityCommand, DeactivateTaxAuthorityResult>
{
    public async Task<DeactivateTaxAuthorityResult> Handle(
        DeactivateTaxAuthorityCommand request,
        CancellationToken cancellationToken)
    {
        var taxAuthority = await repository.GetByIdAsync(request.TaxAuthorityId);
        if (taxAuthority is null)
            throw new InvalidOperationException($"Tax authority with ID {request.TaxAuthorityId} not found.");

        taxAuthority.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTaxAuthorityResult();
    }
}
