using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxAccountingMappingsByCompanyHandler(
    ITaxAccountingMappingRepository repository)
    : IRequestHandler<GetTaxAccountingMappingsByCompanyQuery, IReadOnlyList<TaxAccountingMappingDto>>
{
    public async Task<IReadOnlyList<TaxAccountingMappingDto>> Handle(
        GetTaxAccountingMappingsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxAccountingMappingDto(
                e.Id, e.CompanyId, e.TaxTypeId,
                e.TaxTreatmentId, e.AccountId,
                e.MappingType.ToString(),
                e.IsActive, e.Description))
            .ToList();
    }
}
