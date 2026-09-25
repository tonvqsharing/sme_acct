using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemSupplierPriceHandler(
    IItemSupplierPriceRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemSupplierPriceCommand, CreateItemSupplierPriceResult>
{
    public async Task<CreateItemSupplierPriceResult> Handle(
        CreateItemSupplierPriceCommand request,
        CancellationToken cancellationToken)
    {
        var itemSupplierPrice = new ItemSupplierPrice(
            request.CompanyId,
            request.SupplierId,
            request.ItemId,
            request.UnitPrice,
            request.CurrencyCode,
            request.EffectiveFrom,
            request.EffectiveTo);

        await repository.AddAsync(itemSupplierPrice);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateItemSupplierPriceResult(itemSupplierPrice.Id);
    }
}
