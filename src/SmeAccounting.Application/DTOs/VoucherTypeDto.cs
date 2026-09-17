namespace SmeAccounting.Application.DTOs;

public record VoucherTypeDto(
    long Id,
    string Code,
    string Name,
    string VoucherCategory,
    long CompanyId,
    bool IsActive,
    string? Description);
