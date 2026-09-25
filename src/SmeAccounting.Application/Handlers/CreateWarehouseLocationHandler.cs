using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateWarehouseLocationHandler(
    IWarehouseLocationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateWarehouseLocationCommand, CreateWarehouseLocationResult>
{
    public async Task<CreateWarehouseLocationResult> Handle(CreateWarehouseLocationCommand request, CancellationToken cancellationToken)
    {
        var entity = new SmeAccounting.Domain.Entities.WarehouseLocation(
            request.CompanyId,
            request.WarehouseId,
            request.Code,
            request.Name,
            request.Description);

        await repository.AddAsync(entity);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateWarehouseLocationResult(entity.Id);
    }
}