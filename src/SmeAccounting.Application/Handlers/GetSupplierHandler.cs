using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetSupplierHandler(
    ISupplierRepository repository)
    : IRequestHandler<GetSupplierQuery, SupplierDto?>
{
    public async Task<SupplierDto?> Handle(
        GetSupplierQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.SupplierId);
        return entity is null ? null : new SupplierDto(
            entity.Id,
            entity.CompanyId,
            entity.Code,
            entity.Name,
            entity.TaxCode,
            entity.Address,
            entity.Phone,
            entity.Email,
            entity.PaymentTermId,
            entity.DefaultTaxTypeId,
            entity.IsActive,
            entity.Description);
    }
}
