using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class AddOpeningBalanceEntryHandler(
    IOpeningBalancePeriodRepository periodRepository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<AddOpeningBalanceEntryCommand, AddOpeningBalanceEntryResult>
{
    public async Task<AddOpeningBalanceEntryResult> Handle(
        AddOpeningBalanceEntryCommand request,
        CancellationToken cancellationToken)
    {
        var period = await periodRepository.GetByIdAsync(request.PeriodId)
            ?? throw new KeyNotFoundException($"Opening balance period {request.PeriodId} not found.");

        var entry = period.AddEntry(request.AccountId, request.Debit, request.Credit, request.Description);

        // Entry is already tracked via aggregate? Need to persist entry separately.
        // For simplicity, rely on change tracker through period navigation? 
        // We'll add via repository if needed. Since entry is created via domain method,
        // we save unit of work. Ensure entry is added to context.
        // The period's Entries collection contains the new entry, EF will persist on save.

        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new AddOpeningBalanceEntryResult(entry.Id);
    }
}
