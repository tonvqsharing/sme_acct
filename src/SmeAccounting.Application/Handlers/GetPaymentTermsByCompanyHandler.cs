using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPaymentTermsByCompanyHandler(
    IPaymentTermRepository repository)
    : IRequestHandler<GetPaymentTermsByCompanyQuery, IReadOnlyList<PaymentTermDto>>
{
    public async Task<IReadOnlyList<PaymentTermDto>> Handle(
        GetPaymentTermsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new PaymentTermDto(
                e.Id,
                e.CompanyId,
                e.Code,
                e.Name,
                e.PaymentTermType.ToString(),
                e.Days,
                e.IsActive,
                e.Description))
            .ToList();
    }
}
