using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateWarehouseCommand(
    long CompanyId,
    string Code,
    string Name,
    string? Address = null,
    string? Description = null) : IRequest<CreateWarehouseResult>;

public record CreateWarehouseResult(long Id);
