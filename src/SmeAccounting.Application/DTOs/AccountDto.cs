namespace SmeAccounting.Application.DTOs;

public record AccountDto(
    long Id,
    string Code,
    string Name,
    int Level,
    long? ParentId,
    string AccountType,
    bool IsActive,
    long? AccountGroupId,
    long CompanyId,
    string? Description,
    string NormalBalance);
