namespace SmeAccounting.Application.DTOs;

public record JournalEntryLineDto(
    long Id,
    long AccountId,
    MoneyDto Debit,
    MoneyDto Credit,
    string? Description);
