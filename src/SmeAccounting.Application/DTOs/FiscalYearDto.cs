namespace SmeAccounting.Application.DTOs;

public record FiscalYearDto(
    long Id,
    long CompanyId,
    int Year,
    DateOnly StartDate,
    DateOnly EndDate,
    string? Description,
    string Status);
