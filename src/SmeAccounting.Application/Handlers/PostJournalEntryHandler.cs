using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class PostJournalEntryHandler(
    IJournalEntryRepository journalEntryRepository,
    IUnitOfWork unitOfWork,
    IClock clock)
    : IRequestHandler<PostJournalEntryCommand, PostJournalEntryResult>
{
    public async Task<PostJournalEntryResult> Handle(PostJournalEntryCommand request, CancellationToken cancellationToken)
    {
        var entry = await journalEntryRepository.GetByIdAsync(request.JournalEntryId);
        if (entry is null)
            throw new InvalidOperationException($"Journal entry with ID {request.JournalEntryId} not found.");

        entry.Post("system", clock.Now);

        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new PostJournalEntryResult(entry.Id, entry.PostedAt!.Value);
    }
}