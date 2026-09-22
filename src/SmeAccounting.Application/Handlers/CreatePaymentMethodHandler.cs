using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePaymentMethodHandler(
    IPaymentMethodRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePaymentMethodCommand, CreatePaymentMethodResult>
{
    public async Task<CreatePaymentMethodResult> Handle(
        CreatePaymentMethodCommand request,
        CancellationToken cancellationToken)
    {
        var paymentMethod = new PaymentMethod(
            request.CompanyId,
            request.Code,
            request.Name,
            request.Category,
            request.RequiresBankAccount,
            request.Description);

        await repository.AddAsync(paymentMethod);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePaymentMethodResult(paymentMethod.Id);
    }
}
