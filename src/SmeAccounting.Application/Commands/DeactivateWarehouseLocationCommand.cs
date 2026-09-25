using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateWarehouseLocationCommand(long Id) : IRequest<DeactivateWarehouseLocationResult>;

public record DeactivateWarehouseLocationResult(bool Success);