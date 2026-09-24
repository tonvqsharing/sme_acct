using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreateItemCommand(
    long CompanyId,
    string Code,
    string Name,
    bool IsStockItem,
    bool IsServiceItem,
    long? ItemCategoryId = null,
    long? UomId = null,
    string? Description = null,
    long? ItemGroupId = null) : IRequest<CreateItemResult>;

public record CreateItemResult(long Id);
