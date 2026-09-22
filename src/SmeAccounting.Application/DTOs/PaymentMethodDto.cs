namespace SmeAccounting.Application.DTOs;

public record PaymentMethodDto(
    long Id,
    long CompanyId,
    string Code,
    string Name,
    string Category,
    bool RequiresBankAccount,
    bool IsActive,
    string? Description);
