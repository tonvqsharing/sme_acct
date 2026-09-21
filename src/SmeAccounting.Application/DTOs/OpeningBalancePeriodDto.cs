using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Application.DTOs;

public record OpeningBalancePeriodDto(
    long Id,
    long CompanyId,
    long FiscalPeriodId,
    DateOnly PeriodDate,
    string Status,
    bool IsPosted,
    IReadOnlyCollection<OpeningBalanceEntryDto> Entries);
