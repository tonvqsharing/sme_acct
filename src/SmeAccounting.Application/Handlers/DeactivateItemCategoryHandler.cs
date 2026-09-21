using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateItemCategoryHandler(
    IItemCategoryRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateItemCategoryCommand, DeactivateItemCategoryResult>
{
    public async Task<DeactivateItemCategoryResult> Handle(DeactivateItemCategoryCommand request, CancellationToken cancellationToken)
    {
        var cat = await repository.GetByIdAsync(request.Id);
        if (cat == null) return new DeactivateItemCategoryResult(false);
        cat.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateItemCategoryResult(true);
    }
}
