using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemGroupHandler(IItemGroupRepository repository, IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemGroupCommand, DeactivateItemGroupResult>
{
    public async Task<DeactivateItemGroupResult> Handle(DeactivateItemGroupCommand request, CancellationToken cancellationToken)
    {
        var itemGroup = await repository.GetByIdAsync(request.Id);
        if (itemGroup is null)
            throw new InvalidOperationException($"Item group with ID {request.Id} not found.");

        itemGroup.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateItemGroupResult(true);
    }
}