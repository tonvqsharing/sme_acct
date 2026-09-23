using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class PostOpeningBalancesHandler(
    IOpeningBalancePeriodRepository periodRepository,
    IUnitOfWork unitOfWork,
    IJournalEntryRepository journalEntryRepository,
    IPostingReferenceRepository postingReferenceRepository)
    : IRequestHandler<PostOpeningBalancesCommand, PostOpeningBalancesResult>
{
    public async Task<PostOpeningBalancesResult> Handle(
        PostOpeningBalancesCommand request,
        CancellationToken cancellationToken)
    {
        var period = await periodRepository.GetByIdAsync(request.PeriodId)
            ?? throw new KeyNotFoundException($"Opening balance period {request.PeriodId} not found.");

        var journalEntry = period.PostOpeningBalances(request.PostedBy, request.PostedAt);

        await journalEntryRepository.AddAsync(journalEntry);

        await unitOfWork.SaveChangesAsync(cancellationToken);

        var postingReference = new PostingReference(period.CompanyId, journalEntry.Id, "OpeningBalance", period.Id);
        await postingReferenceRepository.AddAsync(postingReference);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new PostOpeningBalancesResult(true);
    }
}
