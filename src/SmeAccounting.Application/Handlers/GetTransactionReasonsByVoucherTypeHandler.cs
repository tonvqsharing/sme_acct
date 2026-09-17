using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTransactionReasonsByVoucherTypeHandler(
    ITransactionReasonRepository repository)
    : IRequestHandler<GetTransactionReasonsByVoucherTypeQuery, IReadOnlyList<TransactionReasonDto>>
{
    public async Task<IReadOnlyList<TransactionReasonDto>> Handle(
        GetTransactionReasonsByVoucherTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByVoucherTypeAsync(request.VoucherTypeId);
        return entities
            .Select(e => new TransactionReasonDto(
                e.Id, e.Code, e.Name,
                e.VoucherTypeId, e.CompanyId,
                e.IsActive, e.Description))
            .ToList();
    }
}
