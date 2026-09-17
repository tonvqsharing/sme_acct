using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTaxPeriodsByCompanyHandler(
    ITaxPeriodRepository repository)
    : IRequestHandler<GetTaxPeriodsByCompanyQuery, IReadOnlyList<TaxPeriodDto>>
{
    public async Task<IReadOnlyList<TaxPeriodDto>> Handle(
        GetTaxPeriodsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new TaxPeriodDto(
                e.Id, e.CompanyId,
                e.FiscalPeriodId, e.TaxTypeId,
                e.FilingDeadline,
                e.FilingFrequency.ToString(),
                e.Status.ToString(),
                e.IsActive, e.Description))
            .ToList();
    }
}
