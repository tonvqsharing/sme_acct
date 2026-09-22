using MediatR;
using SmeAccounting.Application.BankAccounts.DTOs;

namespace SmeAccounting.Application.BankAccounts.Queries;

public record GetBankAccountsByBankQuery(long BankId) : IRequest<IReadOnlyList<BankAccountDto>>;
