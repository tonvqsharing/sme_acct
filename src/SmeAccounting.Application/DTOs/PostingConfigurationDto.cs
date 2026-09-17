namespace SmeAccounting.Application.DTOs;

public record PostingConfigurationDto(
    long Id,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    long CompanyId,
    long? TransactionReasonId,
    int DisplayOrder,
    bool IsActive,
    string? Description);
