namespace SmeAccounting.Application.DTOs;

public record TaxPeriodDto(
    long Id,
    long CompanyId,
    long FiscalPeriodId,
    long TaxTypeId,
    DateOnly FilingDeadline,
    string FilingFrequency,
    string Status,
    bool IsActive,
    string? Description);
