namespace SmeAccounting.Application.DTOs;

public record JournalEntryDto(
    long Id,
    string EntryNumber,
    DateTimeOffset Date,
    long PeriodId,
    string? Description,
    bool IsPosted,
    DateTimeOffset? PostedAt,
    IReadOnlyList<JournalEntryLineDto> Lines);
