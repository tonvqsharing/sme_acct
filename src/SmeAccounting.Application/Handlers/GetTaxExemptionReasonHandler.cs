using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxExemptionReasonHandler(
    ITaxExemptionReasonRepository repository)
    : IRequestHandler<GetTaxExemptionReasonQuery, TaxExemptionReasonDto?>
{
    public async Task<TaxExemptionReasonDto?> Handle(
        GetTaxExemptionReasonQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxExemptionReasonId);
        return entity is null ? null : new TaxExemptionReasonDto(
            entity.Id, entity.CompanyId, entity.TaxTypeId,
            entity.Code, entity.Name, entity.LegalBasis,
            entity.Description, entity.IsActive);
    }
}
