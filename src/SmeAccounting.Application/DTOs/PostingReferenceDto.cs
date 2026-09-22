namespace SmeAccounting.Application.DTOs;

public record PostingReferenceDto(
    long Id,
    long CompanyId,
    long JournalEntryId,
    string SourceType,
    long SourceId);
