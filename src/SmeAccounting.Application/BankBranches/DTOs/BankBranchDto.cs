namespace SmeAccounting.Application.BankBranches.DTOs;

public record BankBranchDto(
    long Id,
    long CompanyId,
    long BankId,
    string Code,
    string Name,
    bool IsActive,
    string? Description);
