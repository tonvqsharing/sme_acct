using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateWarehouseHandler(
    IWarehouseRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateWarehouseCommand, CreateWarehouseResult>
{
    public async Task<CreateWarehouseResult> Handle(CreateWarehouseCommand request, CancellationToken cancellationToken)
    {
        var wh = new Warehouse(request.CompanyId, request.Code, request.Name, request.Address, request.Description);
        await repository.AddAsync(wh);
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new CreateWarehouseResult(wh.Id);
    }
}
