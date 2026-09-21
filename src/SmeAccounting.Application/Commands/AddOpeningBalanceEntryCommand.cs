using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record AddOpeningBalanceEntryCommand(
    long PeriodId,
    long CompanyId,
    long AccountId,
    Money Debit,
    Money Credit,
    string? Description = null) : IRequest<AddOpeningBalanceEntryResult>;

public record AddOpeningBalanceEntryResult(long Id);
