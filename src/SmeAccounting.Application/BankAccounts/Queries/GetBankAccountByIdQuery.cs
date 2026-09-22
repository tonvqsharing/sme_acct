using MediatR;
using SmeAccounting.Application.BankAccounts.DTOs;

namespace SmeAccounting.Application.BankAccounts.Queries;

public record GetBankAccountByIdQuery(long Id) : IRequest<BankAccountDto?>;
