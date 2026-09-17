using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateSupplierCommand(long SupplierId) : IRequest<DeactivateSupplierResult>;

public record DeactivateSupplierResult;
