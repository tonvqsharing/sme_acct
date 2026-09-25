using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemReorderLevelCommand(
    long CompanyId,
    long ItemId,
    decimal MinimumQuantity,
    long? WarehouseId = null,
    decimal? MaximumQuantity = null) : IRequest<CreateItemReorderLevelResult>;

public record CreateItemReorderLevelResult(long Id);
