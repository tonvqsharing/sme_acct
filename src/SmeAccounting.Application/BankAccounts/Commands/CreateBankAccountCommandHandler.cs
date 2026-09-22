using MediatR;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankAccounts.Commands;

internal sealed class CreateBankAccountCommandHandler(
    IBankAccountRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateBankAccountCommand, CreateBankAccountResult>
{
    public async Task<CreateBankAccountResult> Handle(
        CreateBankAccountCommand request,
        CancellationToken cancellationToken)
    {
        var account = new BankAccount(
            request.CompanyId,
            request.BankId,
            request.Code,
            request.AccountNumber,
            request.AccountName,
            request.BankBranchId,
            request.Description,
            request.CurrencyCode);

        await repository.AddAsync(account);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateBankAccountResult(account.Id);
    }
}
