using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivatePostingConfigurationHandler(
    IPostingConfigurationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivatePostingConfigurationCommand, DeactivatePostingConfigurationResult>
{
    public async Task<DeactivatePostingConfigurationResult> Handle(
        DeactivatePostingConfigurationCommand request,
        CancellationToken cancellationToken)
    {
        var config = await repository.GetByIdAsync(request.ConfigId);
        if (config is null)
            throw new InvalidOperationException($"Posting configuration with ID {request.ConfigId} not found.");

        config.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivatePostingConfigurationResult();
    }
}
