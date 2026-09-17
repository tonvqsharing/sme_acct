using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePaymentTermHandler(
    IPaymentTermRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePaymentTermCommand, CreatePaymentTermResult>
{
    public async Task<CreatePaymentTermResult> Handle(
        CreatePaymentTermCommand request,
        CancellationToken cancellationToken)
    {
        var paymentTerm = new PaymentTerm(
            request.CompanyId,
            request.Code,
            request.Name,
            request.PaymentTermType,
            request.Days,
            request.Description);

        await repository.AddAsync(paymentTerm);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePaymentTermResult(paymentTerm.Id);
    }
}
