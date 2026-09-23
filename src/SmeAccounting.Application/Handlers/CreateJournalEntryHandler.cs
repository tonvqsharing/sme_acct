using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateJournalEntryHandler(
    IVoucherTypeRepository voucherTypeRepository,
    IDocumentNumberingSeriesRepository numberingSeriesRepository,
    IJournalEntryRepository journalEntryRepository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateJournalEntryCommand, CreateJournalEntryResult>
{
    public async Task<CreateJournalEntryResult> Handle(
        CreateJournalEntryCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = await voucherTypeRepository.GetByCodeAsync("JNRL", request.CompanyId);
        if (voucherType is null)
            throw new InvalidOperationException($"No voucher type with code JNRL for company {request.CompanyId}.");

        var series = await numberingSeriesRepository.GetDefaultAsync(voucherType.Id, request.CompanyId);
        if (series is null)
            throw new InvalidOperationException($"No default numbering series for voucher type {voucherType.Id} of company {request.CompanyId}.");

        var entryNumber = $"{series.Prefix}{series.NextNumber.ToString($"D{series.PaddingLength}")}";
        series.Increment();

        var entry = new JournalEntry(entryNumber, request.Date, request.PeriodId, request.Description);
        foreach (var line in request.Lines)
        {
            entry.AddLine(
                line.AccountId,
                new Money(line.DebitAmount, "VND"),
                new Money(line.CreditAmount, "VND"),
                line.Description);
        }

        await journalEntryRepository.AddAsync(entry);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateJournalEntryResult(entry.Id, entry.EntryNumber);
    }
}