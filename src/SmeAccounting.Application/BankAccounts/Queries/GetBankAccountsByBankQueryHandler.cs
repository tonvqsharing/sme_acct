using MediatR;
using SmeAccounting.Application.BankAccounts.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.BankAccounts.Queries;

internal sealed class GetBankAccountsByBankQueryHandler(
    IBankAccountRepository repository)
    : IRequestHandler<GetBankAccountsByBankQuery, IReadOnlyList<BankAccountDto>>
{
    public async Task<IReadOnlyList<BankAccountDto>> Handle(
        GetBankAccountsByBankQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByBankAsync(request.BankId);
        return entities.Select(e => new BankAccountDto(
            e.Id,
            e.CompanyId,
            e.BankId,
            e.BankBranchId,
            e.Code,
            e.AccountNumber,
            e.AccountName,
            e.IsActive,
            e.Description,
            e.CurrencyCode)).ToList();
    }
}
