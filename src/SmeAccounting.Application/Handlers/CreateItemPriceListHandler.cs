using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemPriceListHandler(
    IItemPriceListRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemPriceListCommand, CreateItemPriceListResult>
{
    public async Task<CreateItemPriceListResult> Handle(
        CreateItemPriceListCommand request,
        CancellationToken cancellationToken)
    {
        var itemPriceList = new ItemPriceList(
            request.CompanyId,
            request.PriceListId,
            request.ItemId,
            request.UnitPrice,
            request.CurrencyCode,
            request.EffectiveFrom,
            request.EffectiveTo);

        await repository.AddAsync(itemPriceList);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateItemPriceListResult(itemPriceList.Id);
    }
}