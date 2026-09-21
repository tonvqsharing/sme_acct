using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateUomHandler(
    IUomRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateUomCommand, DeactivateUomResult>
{
    public async Task<DeactivateUomResult> Handle(DeactivateUomCommand request, CancellationToken cancellationToken)
    {
        var uom = await repository.GetByIdAsync(request.Id);
        if (uom == null) return new DeactivateUomResult(false);
        uom.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateUomResult(true);
    }
}
