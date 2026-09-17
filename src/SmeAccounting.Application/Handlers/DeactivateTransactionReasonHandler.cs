using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTransactionReasonHandler(
    ITransactionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTransactionReasonCommand, DeactivateTransactionReasonResult>
{
    public async Task<DeactivateTransactionReasonResult> Handle(
        DeactivateTransactionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var reason = await repository.GetByIdAsync(request.ReasonId);
        if (reason is null)
            throw new InvalidOperationException($"Transaction reason with ID {request.ReasonId} not found.");

        reason.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTransactionReasonResult();
    }
}
