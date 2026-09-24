namespace SmeAccounting.Application.DTOs;

public record ItemBarcodeDto(
    long Id,
    long CompanyId,
    long ItemId,
    string Barcode,
    string BarcodeType,
    long? UomId,
    bool IsPrimary,
    bool IsActive);