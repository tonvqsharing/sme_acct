using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateCustomerHandler(
    ICustomerRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateCustomerCommand, DeactivateCustomerResult>
{
    public async Task<DeactivateCustomerResult> Handle(
        DeactivateCustomerCommand request,
        CancellationToken cancellationToken)
    {
        var customer = await repository.GetByIdAsync(request.CustomerId);
        if (customer is null)
            throw new InvalidOperationException($"Customer with ID {request.CustomerId} not found.");

        customer.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateCustomerResult();
    }
}
