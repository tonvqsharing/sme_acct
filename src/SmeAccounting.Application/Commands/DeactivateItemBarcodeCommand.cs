using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemBarcodeCommand(long Id) : IRequest<DeactivateItemBarcodeResult>;

public record DeactivateItemBarcodeResult(bool Success);