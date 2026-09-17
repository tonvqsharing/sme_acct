using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateEmployeeHandler(
    IEmployeeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateEmployeeCommand, CreateEmployeeResult>
{
    public async Task<CreateEmployeeResult> Handle(
        CreateEmployeeCommand request,
        CancellationToken cancellationToken)
    {
        var employee = new Employee(
            request.CompanyId,
            request.Code,
            request.Name,
            request.EmployeeNumber,
            request.TaxCode,
            request.Address,
            request.Phone,
            request.Email,
            request.HireDate,
            request.Description);

        await repository.AddAsync(employee);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateEmployeeResult(employee.Id);
    }
}
