using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateItemTaxClassHandler(
    IItemTaxClassRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateItemTaxClassCommand, CreateItemTaxClassResult>
{
    public async Task<CreateItemTaxClassResult> Handle(CreateItemTaxClassCommand request, CancellationToken cancellationToken)
    {
        var entity = new SmeAccounting.Domain.Entities.ItemTaxClass(
            request.CompanyId,
            request.ItemId,
            request.TaxTypeId,
            request.EffectiveFrom,
            request.EffectiveTo);

        await repository.AddAsync(entity);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateItemTaxClassResult(entity.Id);
    }
}