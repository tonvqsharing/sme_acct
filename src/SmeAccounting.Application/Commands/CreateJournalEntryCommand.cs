using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Commands;

public record CreateJournalEntryCommand(
    DateTimeOffset Date,
    long PeriodId,
    string? Description,
    string? SourceType,
    long? SourceId,
    IReadOnlyList<JournalEntryLineInput> Lines) : IRequest<CreateJournalEntryResult>;

public record JournalEntryLineInput(
    long AccountId,
    decimal DebitAmount,
    decimal CreditAmount,
    string? Description);

public record CreateJournalEntryResult(long Id, string EntryNumber);
