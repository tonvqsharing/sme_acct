using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateItemBarcodeCommand(
    long CompanyId,
    long ItemId,
    string Barcode,
    BarcodeType BarcodeType,
    long? UomId = null,
    bool IsPrimary = false) : IRequest<CreateItemBarcodeResult>;

public record CreateItemBarcodeResult(long Id);