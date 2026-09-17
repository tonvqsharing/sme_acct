namespace SmeAccounting.Application.DTOs;

public record TransactionReasonDto(
    long Id,
    string Code,
    string Name,
    long VoucherTypeId,
    long CompanyId,
    bool IsActive,
    string? Description);
