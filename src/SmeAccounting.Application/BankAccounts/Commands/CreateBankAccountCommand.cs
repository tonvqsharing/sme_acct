using MediatR;

namespace SmeAccounting.Application.BankAccounts.Commands;

public record CreateBankAccountCommand(
    long CompanyId,
    long BankId,
    string Code,
    string AccountNumber,
    string AccountName,
    long? BankBranchId = null,
    string? Description = null,
    string? CurrencyCode = null) : IRequest<CreateBankAccountResult>;

public record CreateBankAccountResult(long Id);
