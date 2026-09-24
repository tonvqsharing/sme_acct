using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateUomClassHandler(
    IUomClassRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateUomClassCommand, DeactivateUomClassResult>
{
    public async Task<DeactivateUomClassResult> Handle(DeactivateUomClassCommand request, CancellationToken cancellationToken)
    {
        var uomClass = await repository.GetByIdAsync(request.Id);
        if (uomClass is null)
            throw new InvalidOperationException($"Uom class with ID {request.Id} not found.");

        uomClass.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateUomClassResult();
    }
}