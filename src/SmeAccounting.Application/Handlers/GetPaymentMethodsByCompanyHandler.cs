using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPaymentMethodsByCompanyHandler(
    IPaymentMethodRepository repository)
    : IRequestHandler<GetPaymentMethodsByCompanyQuery, IReadOnlyList<PaymentMethodDto>>
{
    public async Task<IReadOnlyList<PaymentMethodDto>> Handle(
        GetPaymentMethodsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new PaymentMethodDto(
                e.Id,
                e.CompanyId,
                e.Code,
                e.Name,
                e.Category.ToString(),
                e.RequiresBankAccount,
                e.IsActive,
                e.Description))
            .ToList();
    }
}
