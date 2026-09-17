using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetEmployeeHandler(
    IEmployeeRepository repository)
    : IRequestHandler<GetEmployeeQuery, EmployeeDto?>
{
    public async Task<EmployeeDto?> Handle(
        GetEmployeeQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.EmployeeId);
        return entity is null ? null : new EmployeeDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.EmployeeNumber,
            entity.TaxCode,
            entity.Address,
            entity.Phone,
            entity.Email,
            entity.HireDate,
            entity.IsActive,
            entity.Description);
    }
}
