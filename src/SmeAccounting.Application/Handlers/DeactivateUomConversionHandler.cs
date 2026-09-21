using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateUomConversionHandler(
    IUomConversionRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateUomConversionCommand, DeactivateUomConversionResult>
{
    public async Task<DeactivateUomConversionResult> Handle(DeactivateUomConversionCommand request, CancellationToken cancellationToken)
    {
        var conv = await repository.GetByIdAsync(request.Id);
        if (conv == null) return new DeactivateUomConversionResult(false);
        conv.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);
        return new DeactivateUomConversionResult(true);
    }
}
