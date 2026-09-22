using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivatePaymentMethodHandler(
    IPaymentMethodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivatePaymentMethodCommand, DeactivatePaymentMethodResult>
{
    public async Task<DeactivatePaymentMethodResult> Handle(
        DeactivatePaymentMethodCommand request,
        CancellationToken cancellationToken)
    {
        var paymentMethod = await repository.GetByIdAsync(request.PaymentMethodId);
        if (paymentMethod is null)
            throw new InvalidOperationException($"Payment method with ID {request.PaymentMethodId} not found.");

        paymentMethod.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivatePaymentMethodResult();
    }
}
