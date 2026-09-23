using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetJournalEntriesQueryHandler(
    IJournalEntryRepository repository)
    : IRequestHandler<GetJournalEntriesQuery, IReadOnlyList<JournalEntryDto>>
{
    public async Task<IReadOnlyList<JournalEntryDto>> Handle(
        GetJournalEntriesQuery request,
        CancellationToken cancellationToken)
    {
        var entries = await repository.GetAllAsync();
        return entries
            .Select(e => new JournalEntryDto(
                e.Id,
                e.EntryNumber,
                e.Date,
                e.PeriodId,
                e.Description,
                e.IsPosted,
                e.PostedAt,
                e.Lines
                    .Select(l => new JournalEntryLineDto(
                        l.Id,
                        l.AccountId,
                        new MoneyDto(l.Debit.Amount, l.Debit.Currency),
                        new MoneyDto(l.Credit.Amount, l.Credit.Currency),
                        l.Description,
                        l.DepartmentId,
                        l.CostCenterId,
                        l.ProjectId))
                    .ToList()))
            .ToList();
    }
}