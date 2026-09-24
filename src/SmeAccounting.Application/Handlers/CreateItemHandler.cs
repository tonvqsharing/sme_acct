using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemHandler(IItemRepository repository, IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemCommand, CreateItemResult>
{
    public async Task<CreateItemResult> Handle(CreateItemCommand request, CancellationToken cancellationToken)
    {
        var item = new Item(request.CompanyId, request.Code, request.Name, request.IsStockItem, request.IsServiceItem, request.ItemCategoryId, request.UomId, request.Description, request.ItemGroupId);
        await repository.AddAsync(item);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateItemResult(item.Id);
    }
}
