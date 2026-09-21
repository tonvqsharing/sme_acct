using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemHandler(IItemRepository repository, IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemCommand, DeactivateItemResult>
{
    public async Task<DeactivateItemResult> Handle(DeactivateItemCommand request, CancellationToken cancellationToken)
    {
        var item = await repository.GetByIdAsync(request.Id);
        if (item == null) return new DeactivateItemResult(false);
        item.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateItemResult(true);
    }
}
