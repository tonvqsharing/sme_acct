namespace SmeAccounting.Application.DTOs;

public record PaymentTermDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string PaymentTermType,
    int? Days,
    bool IsActive,
    string? Description);
