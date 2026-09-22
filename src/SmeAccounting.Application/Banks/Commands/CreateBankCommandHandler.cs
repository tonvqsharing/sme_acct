using MediatR;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Banks.Commands;

internal sealed class CreateBankCommandHandler(
    IBankRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateBankCommand, CreateBankResult>
{
    public async Task<CreateBankResult> Handle(
        CreateBankCommand request,
        CancellationToken cancellationToken)
    {
        var bank = new Bank(
            request.CompanyId,
            request.Code,
            request.Name,
            request.Description);

        await repository.AddAsync(bank);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateBankResult(bank.Id);
    }
}
