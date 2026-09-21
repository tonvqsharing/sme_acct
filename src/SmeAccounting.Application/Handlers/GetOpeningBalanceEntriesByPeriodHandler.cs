using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalanceEntriesByPeriodHandler(
    IOpeningBalanceEntryRepository repository)
    : IRequestHandler<GetOpeningBalanceEntriesByPeriodQuery, IReadOnlyList<OpeningBalanceEntryDto>>
{
    public async Task<IReadOnlyList<OpeningBalanceEntryDto>> Handle(
        GetOpeningBalanceEntriesByPeriodQuery request,
        CancellationToken cancellationToken)
    {
        var entries = await repository.GetAllByPeriodAsync(request.PeriodId);

        return entries.Select(e => new OpeningBalanceEntryDto(
            e.Id,
            e.OpeningBalancePeriodId,
            e.CompanyId,
            e.AccountId,
            e.Debit.Amount,
            e.Debit.Currency,
            e.Credit.Amount,
            e.Credit.Currency,
            e.Description)).ToList();
    }
}
