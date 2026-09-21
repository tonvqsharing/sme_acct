using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalancePeriodByIdHandler(
    IOpeningBalancePeriodRepository repository)
    : IRequestHandler<GetOpeningBalancePeriodByIdQuery, OpeningBalancePeriodDto?>
{
    public async Task<OpeningBalancePeriodDto?> Handle(
        GetOpeningBalancePeriodByIdQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.PeriodId);
        if (entity is null) return null;

        var entries = entity.Entries.Select(e => new OpeningBalanceEntryDto(
            e.Id,
            e.OpeningBalancePeriodId,
            e.CompanyId,
            e.AccountId,
            e.Debit.Amount,
            e.Debit.Currency,
            e.Credit.Amount,
            e.Credit.Currency,
            e.Description)).ToList();

        return new OpeningBalancePeriodDto(
            entity.Id,
            entity.CompanyId,
            entity.FiscalPeriodId,
            entity.PeriodDate,
            entity.Status.ToString(),
            entity.IsPosted,
            entries);
    }
}
