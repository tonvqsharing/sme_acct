using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemPriceListHandler(
    IItemPriceListRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemPriceListCommand, DeactivateItemPriceListResult>
{
    public async Task<DeactivateItemPriceListResult> Handle(
        DeactivateItemPriceListCommand request,
        CancellationToken cancellationToken)
    {
        var itemPriceList = await repository.GetByIdAsync(request.Id);
        if (itemPriceList is null)
            throw new InvalidOperationException($"Item price list with ID {request.Id} not found.");

        itemPriceList.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateItemPriceListResult(true);
    }
}