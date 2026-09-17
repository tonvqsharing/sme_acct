using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingConfigurationHandler(
    IPostingConfigurationRepository repository)
    : IRequestHandler<GetPostingConfigurationQuery, PostingConfigurationDto?>
{
    public async Task<PostingConfigurationDto?> Handle(
        GetPostingConfigurationQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.ConfigId);
        return entity is null ? null : new PostingConfigurationDto(
            entity.Id, entity.VoucherTypeId, entity.DebitAccountId,
            entity.CreditAccountId, entity.CompanyId,
            entity.TransactionReasonId, entity.DisplayOrder,
            entity.IsActive, entity.Description);
    }
}
