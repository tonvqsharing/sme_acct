namespace SmeAccounting.Application.Banks.DTOs;

public record BankDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);
