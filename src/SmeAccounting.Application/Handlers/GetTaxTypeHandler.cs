using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxTypeHandler(
    ITaxTypeRepository repository)
    : IRequestHandler<GetTaxTypeQuery, TaxTypeDto?>
{
    public async Task<TaxTypeDto?> Handle(
        GetTaxTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxTypeId);
        return entity is null ? null : new TaxTypeDto(
            entity.Id, entity.Code, entity.Name,
            entity.TaxCategory.ToString(),
            entity.CompanyId, entity.IsActive, entity.Description);
    }
}
