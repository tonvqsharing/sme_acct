namespace SmeAccounting.Application.DTOs;

public record FiscalYearDto(
    long Id,
    int Year,
    string Status);
