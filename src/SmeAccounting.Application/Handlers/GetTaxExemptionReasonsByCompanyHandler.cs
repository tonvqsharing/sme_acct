using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxExemptionReasonsByCompanyHandler(
    ITaxExemptionReasonRepository repository)
    : IRequestHandler<GetTaxExemptionReasonsByCompanyQuery, IReadOnlyList<TaxExemptionReasonDto>>
{
    public async Task<IReadOnlyList<TaxExemptionReasonDto>> Handle(
        GetTaxExemptionReasonsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxExemptionReasonDto(
                e.Id, e.CompanyId, e.TaxTypeId,
                e.Code, e.Name, e.LegalBasis,
                e.Description, e.IsActive))
            .ToList();
    }
}
