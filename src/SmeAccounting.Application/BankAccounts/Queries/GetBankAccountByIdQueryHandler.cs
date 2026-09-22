using MediatR;
using SmeAccounting.Application.BankAccounts.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankAccounts.Queries;

internal sealed class GetBankAccountByIdQueryHandler(
    IBankAccountRepository repository)
    : IRequestHandler<GetBankAccountByIdQuery, BankAccountDto?>
{
    public async Task<BankAccountDto?> Handle(
        GetBankAccountByIdQuery request,
        CancellationToken cancellationToken)
    {
        var account = await repository.GetByIdAsync(request.Id);
        if (account is null) return null;

        return new BankAccountDto(
            account.Id,
            account.CompanyId,
            account.BankId,
            account.BankBranchId,
            account.Code,
            account.AccountNumber,
            account.AccountName,
            account.IsActive,
            account.Description,
            account.CurrencyCode);
    }
}
