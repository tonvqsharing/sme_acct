using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxTypesByCompanyHandler(
    ITaxTypeRepository repository)
    : IRequestHandler<GetTaxTypesByCompanyQuery, IReadOnlyList<TaxTypeDto>>
{
    public async Task<IReadOnlyList<TaxTypeDto>> Handle(
        GetTaxTypesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxTypeDto(
                e.Id, e.Code, e.Name,
                e.TaxCategory.ToString(),
                e.CompanyId, e.IsActive, e.Description))
            .ToList();
    }
}
