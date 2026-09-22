using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPaymentMethodHandler(
    IPaymentMethodRepository repository)
    : IRequestHandler<GetPaymentMethodQuery, PaymentMethodDto?>
{
    public async Task<PaymentMethodDto?> Handle(
        GetPaymentMethodQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.PaymentMethodId);
        return entity is null ? null : new PaymentMethodDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.Category.ToString(),
            entity.RequiresBankAccount,
            entity.IsActive,
            entity.Description);
    }
}
