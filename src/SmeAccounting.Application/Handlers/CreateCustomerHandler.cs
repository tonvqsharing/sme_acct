using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateCustomerHandler(
    ICustomerRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateCustomerCommand, CreateCustomerResult>
{
    public async Task<CreateCustomerResult> Handle(
        CreateCustomerCommand request,
        CancellationToken cancellationToken)
    {
        var customer = new Customer(
            request.CompanyId,
            request.Code,
            request.Name,
            request.TaxCode,
            request.Address,
            request.Phone,
            request.Email,
            request.Description);

        await repository.AddAsync(customer);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateCustomerResult(customer.Id);
    }
}
