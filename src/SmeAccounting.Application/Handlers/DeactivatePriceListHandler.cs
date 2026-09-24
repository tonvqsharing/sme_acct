using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivatePriceListHandler(
    IPriceListRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivatePriceListCommand, DeactivatePriceListResult>
{
    public async Task<DeactivatePriceListResult> Handle(
        DeactivatePriceListCommand request,
        CancellationToken cancellationToken)
    {
        var priceList = await repository.GetByIdAsync(request.Id);
        if (priceList is null)
            throw new InvalidOperationException($"Price list with ID {request.Id} not found.");

        priceList.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivatePriceListResult(true);
    }
}