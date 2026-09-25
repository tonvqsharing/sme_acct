using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateItemSupplierPriceCommand(long Id) : IRequest<DeactivateItemSupplierPriceResult>;

public record DeactivateItemSupplierPriceResult(bool Success);
