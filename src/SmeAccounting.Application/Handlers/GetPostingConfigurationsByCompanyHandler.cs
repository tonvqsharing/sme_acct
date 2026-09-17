using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingConfigurationsByCompanyHandler(
    IPostingConfigurationRepository repository)
    : IRequestHandler<GetPostingConfigurationsByCompanyQuery, IReadOnlyList<PostingConfigurationDto>>
{
    public async Task<IReadOnlyList<PostingConfigurationDto>> Handle(
        GetPostingConfigurationsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new PostingConfigurationDto(
                e.Id, e.VoucherTypeId, e.DebitAccountId,
                e.CreditAccountId, e.CompanyId,
                e.TransactionReasonId, e.DisplayOrder,
                e.IsActive, e.Description))
            .ToList();
    }
}
