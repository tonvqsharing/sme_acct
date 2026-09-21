using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeactivateWarehouseCommand(long Id) : IRequest<DeactivateWarehouseResult>;

public record DeactivateWarehouseResult(bool Success);
