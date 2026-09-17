using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxPeriodHandler(
    ITaxPeriodRepository repository)
    : IRequestHandler<GetTaxPeriodQuery, TaxPeriodDto?>
{
    public async Task<TaxPeriodDto?> Handle(
        GetTaxPeriodQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.TaxPeriodId);
        return entity is null ? null : new TaxPeriodDto(
            entity.Id, entity.CompanyId,
            entity.FiscalPeriodId, entity.TaxTypeId,
            entity.FilingDeadline,
            entity.FilingFrequency.ToString(),
            entity.Status.ToString(),
            entity.IsActive, entity.Description);
    }
}
