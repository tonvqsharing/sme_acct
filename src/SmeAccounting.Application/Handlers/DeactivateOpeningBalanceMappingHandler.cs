using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateOpeningBalanceMappingCommand, DeactivateOpeningBalanceMappingResult>
{
    public async Task<DeactivateOpeningBalanceMappingResult> Handle(
        DeactivateOpeningBalanceMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = await repository.GetByIdAsync(request.MappingId);
        if (mapping is null)
            throw new InvalidOperationException($"Opening balance mapping with ID {request.MappingId} not found.");

        mapping.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateOpeningBalanceMappingResult();
    }
}
