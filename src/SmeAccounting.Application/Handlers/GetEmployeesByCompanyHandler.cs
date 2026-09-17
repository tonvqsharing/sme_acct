using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetEmployeesByCompanyHandler(
    IEmployeeRepository repository)
    : IRequestHandler<GetEmployeesByCompanyQuery, IReadOnlyList<EmployeeDto>>
{
    public async Task<IReadOnlyList<EmployeeDto>> Handle(
        GetEmployeesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new EmployeeDto(
                e.Id,
                e.CompanyId,
                e.Code,
                e.Name,
                e.EmployeeNumber,
                e.TaxCode,
                e.Address,
                e.Phone,
                e.Email,
                e.HireDate,
                e.IsActive,
                e.Description))
            .ToList();
    }
}
