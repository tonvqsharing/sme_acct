using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateWarehouseLocationCommand(
    long CompanyId,
    long WarehouseId,
    string Code,
    string Name,
    string? Description = null)
    : IRequest<CreateWarehouseLocationResult>;

public record CreateWarehouseLocationResult(long Id);