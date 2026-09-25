using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemReorderLevelHandler(
    IItemReorderLevelRepository repository,
    IItemRepository itemRepository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemReorderLevelCommand, CreateItemReorderLevelResult>
{
    public async Task<CreateItemReorderLevelResult> Handle(CreateItemReorderLevelCommand request, CancellationToken cancellationToken)
    {
        var item = await itemRepository.GetByIdAsync(request.ItemId);
        if (item == null)
            throw new InvalidOperationException($"Item with ID {request.ItemId} not found.");

        if (!item.IsStockItem)
            throw new DomainException("Item must be a stock item to have reorder level.");

        var reorderLevel = new ItemReorderLevel(request.CompanyId, request.ItemId, request.MinimumQuantity, request.WarehouseId, request.MaximumQuantity);
        await repository.AddAsync(reorderLevel);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateItemReorderLevelResult(reorderLevel.Id);
    }
}
