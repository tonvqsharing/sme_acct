using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemReorderLevelHandler(
    IItemReorderLevelRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemReorderLevelCommand, DeactivateItemReorderLevelResult>
{
    public async Task<DeactivateItemReorderLevelResult> Handle(DeactivateItemReorderLevelCommand request, CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.Id);
        if (entity == null)
            throw new InvalidOperationException($"Item reorder level with ID {request.Id} not found.");

        entity.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateItemReorderLevelResult(true);
    }
}
