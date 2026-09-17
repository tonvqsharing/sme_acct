using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxTreatmentHandler(
    ITaxTreatmentRepository repository)
    : IRequestHandler<GetTaxTreatmentQuery, TaxTreatmentDto?>
{
    public async Task<TaxTreatmentDto?> Handle(
        GetTaxTreatmentQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxTreatmentId);
        return entity is null ? null : new TaxTreatmentDto(
            entity.Id, entity.Code, entity.Name,
            entity.TaxTypeId, entity.TaxTreatmentType.ToString(),
            entity.InputCreditAllowed, entity.CompanyId,
            entity.IsActive, entity.Description);
    }
}
