using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetSuppliersByCompanyHandler(
    ISupplierRepository repository)
    : IRequestHandler<GetSuppliersByCompanyQuery, IReadOnlyList<SupplierDto>>
{
    public async Task<IReadOnlyList<SupplierDto>> Handle(
        GetSuppliersByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new SupplierDto(
                e.Id,
                e.CompanyId,
                e.Code,
                e.Name,
                e.TaxCode,
                e.Address,
                e.Phone,
                e.Email,
                e.PaymentTermId,
                e.DefaultTaxTypeId,
                e.IsActive,
                e.Description))
            .ToList();
    }
}
