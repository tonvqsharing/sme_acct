namespace SmeAccounting.Application.DTOs;

public record FiscalPeriodDto(
    long Id,
    long YearId,
    int Month,
    DateOnly StartDate,
    DateOnly EndDate,
    string PeriodType,
    string Status,
    DateTimeOffset? OpenedAt,
    DateTimeOffset? ClosedAt);
