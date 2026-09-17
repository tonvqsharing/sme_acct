namespace SmeAccounting.Application.DTOs;

public record OpeningBalanceMappingDto(
    long Id,
    long CompanyId,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    bool IsActive,
    string? Description);
