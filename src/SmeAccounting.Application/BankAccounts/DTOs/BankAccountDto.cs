namespace SmeAccounting.Application.BankAccounts.DTOs;

public record BankAccountDto(
    long Id,
    long CompanyId,
    long BankId,
    long? BankBranchId,
    string Code,
    string AccountNumber,
    string AccountName,
    bool IsActive,
    string? Description,
    string? CurrencyCode);
