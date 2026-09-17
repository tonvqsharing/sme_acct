using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetCustomersByCompanyHandler(
    ICustomerRepository repository)
    : IRequestHandler<GetCustomersByCompanyQuery, IReadOnlyList<CustomerDto>>
{
    public async Task<IReadOnlyList<CustomerDto>> Handle(
        GetCustomersByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new CustomerDto(
                e.Id,
                e.CompanyId,
                e.Code,
                e.Name,
                e.TaxCode,
                e.Address,
                e.Phone,
                e.Email,
                e.IsActive,
                e.Description))
            .ToList();
    }
}
