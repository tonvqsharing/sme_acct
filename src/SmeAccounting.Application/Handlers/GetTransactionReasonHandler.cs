using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTransactionReasonHandler(
    ITransactionReasonRepository repository)
    : IRequestHandler<GetTransactionReasonQuery, TransactionReasonDto?>
{
    public async Task<TransactionReasonDto?> Handle(
        GetTransactionReasonQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.ReasonId);
        return entity is null ? null : new TransactionReasonDto(
            entity.Id, entity.Code, entity.Name,
            entity.VoucherTypeId, entity.CompanyId,
            entity.IsActive, entity.Description);
    }
}
