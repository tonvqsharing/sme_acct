namespace SmeAccounting.Application.DTOs;

public record OpeningBalanceEntryDto(
    long Id,
    long OpeningBalancePeriodId,
    long CompanyId,
    long AccountId,
    decimal DebitAmount,
    string DebitCurrency,
    decimal CreditAmount,
    string CreditCurrency,
    string? Description);
