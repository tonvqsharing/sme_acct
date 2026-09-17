namespace SmeAccounting.Application.DTOs;

public record DocumentNumberingSeriesDto(
    long Id,
    long VoucherTypeId,
    long CompanyId,
    string Prefix,
    int NextNumber,
    int PaddingLength,
    bool IsDefault,
    bool IsActive,
    string? Description);
