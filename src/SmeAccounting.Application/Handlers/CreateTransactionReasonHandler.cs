using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTransactionReasonHandler(
    ITransactionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTransactionReasonCommand, CreateTransactionReasonResult>
{
    public async Task<CreateTransactionReasonResult> Handle(
        CreateTransactionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var reason = new TransactionReason(
            request.CompanyId, request.VoucherTypeId,
            request.Code, request.Name, request.Description);

        await repository.AddAsync(reason);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTransactionReasonResult(reason.Id);
    }
}
