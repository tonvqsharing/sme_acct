using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivatePaymentTermHandler(
    IPaymentTermRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivatePaymentTermCommand, DeactivatePaymentTermResult>
{
    public async Task<DeactivatePaymentTermResult> Handle(
        DeactivatePaymentTermCommand request,
        CancellationToken cancellationToken)
    {
        var paymentTerm = await repository.GetByIdAsync(request.PaymentTermId);
        if (paymentTerm is null)
            throw new InvalidOperationException($"Payment term with ID {request.PaymentTermId} not found.");

        paymentTerm.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivatePaymentTermResult();
    }
}
