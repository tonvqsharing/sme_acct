using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetCustomerHandler(
    ICustomerRepository repository)
    : IRequestHandler<GetCustomerQuery, CustomerDto?>
{
    public async Task<CustomerDto?> Handle(
        GetCustomerQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.CustomerId);
        return entity is null ? null : new CustomerDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.TaxCode,
            entity.Address,
            entity.Phone,
            entity.Email,
            entity.IsActive,
            entity.Description);
    }
}
