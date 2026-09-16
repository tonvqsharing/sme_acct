namespace SmeAccounting.Application.DTOs;

public record FiscalPeriodDto(
    long Id,
    long YearId,
    int Month,
    string Status,
    DateTimeOffset? OpenedAt,
    DateTimeOffset? ClosedAt);
