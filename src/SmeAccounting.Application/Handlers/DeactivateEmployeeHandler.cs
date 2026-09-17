using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateEmployeeHandler(
    IEmployeeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateEmployeeCommand, DeactivateEmployeeResult>
{
    public async Task<DeactivateEmployeeResult> Handle(
        DeactivateEmployeeCommand request,
        CancellationToken cancellationToken)
    {
        var employee = await repository.GetByIdAsync(request.EmployeeId);
        if (employee is null)
            throw new InvalidOperationException($"Employee with ID {request.EmployeeId} not found.");

        employee.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateEmployeeResult();
    }
}
