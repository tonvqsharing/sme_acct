using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPaymentTermHandler(
    IPaymentTermRepository repository)
    : IRequestHandler<GetPaymentTermQuery, PaymentTermDto?>
{
    public async Task<PaymentTermDto?> Handle(
        GetPaymentTermQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.PaymentTermId);
        return entity is null ? null : new PaymentTermDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.PaymentTermType.ToString(),
            entity.Days,
            entity.IsActive,
            entity.Description);
    }
}
