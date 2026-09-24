using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePriceListHandler(
    IPriceListRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePriceListCommand, CreatePriceListResult>
{
    public async Task<CreatePriceListResult> Handle(
        CreatePriceListCommand request,
        CancellationToken cancellationToken)
    {
        var priceList = new PriceList(
            request.CompanyId,
            request.Code,
            request.Name,
            request.Description);

        await repository.AddAsync(priceList);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePriceListResult(priceList.Id);
    }
}