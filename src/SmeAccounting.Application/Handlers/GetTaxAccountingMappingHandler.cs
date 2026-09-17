using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxAccountingMappingHandler(
    ITaxAccountingMappingRepository repository)
    : IRequestHandler<GetTaxAccountingMappingQuery, TaxAccountingMappingDto?>
{
    public async Task<TaxAccountingMappingDto?> Handle(
        GetTaxAccountingMappingQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxAccountingMappingId);
        return entity is null ? null : new TaxAccountingMappingDto(
            entity.Id, entity.CompanyId, entity.TaxTypeId,
            entity.TaxTreatmentId, entity.AccountId,
            entity.MappingType.ToString(),
            entity.IsActive, entity.Description);
    }
}
