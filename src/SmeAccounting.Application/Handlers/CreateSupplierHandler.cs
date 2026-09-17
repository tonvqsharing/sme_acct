using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateSupplierHandler(
    ISupplierRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateSupplierCommand, CreateSupplierResult>
{
    public async Task<CreateSupplierResult> Handle(
        CreateSupplierCommand request,
        CancellationToken cancellationToken)
    {
        var supplier = new Supplier(
            request.CompanyId,
            request.Code,
            request.Name,
            request.TaxCode,
            request.Address,
            request.Phone,
            request.Email,
            request.PaymentTermId,
            request.DefaultTaxTypeId,
            request.Description);

        await repository.AddAsync(supplier);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateSupplierResult(supplier.Id);
    }
}
