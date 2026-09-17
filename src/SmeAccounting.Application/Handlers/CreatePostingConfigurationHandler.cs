using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePostingConfigurationHandler(
    IPostingConfigurationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePostingConfigurationCommand, CreatePostingConfigurationResult>
{
    public async Task<CreatePostingConfigurationResult> Handle(
        CreatePostingConfigurationCommand request,
        CancellationToken cancellationToken)
    {
        var config = new PostingConfiguration(
            request.CompanyId, request.VoucherTypeId,
            request.DebitAccountId, request.CreditAccountId,
            request.TransactionReasonId, description: request.Description);

        await repository.AddAsync(config);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePostingConfigurationResult(config.Id);
    }
}
