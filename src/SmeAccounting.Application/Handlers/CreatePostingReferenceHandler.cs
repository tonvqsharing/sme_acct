using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePostingReferenceHandler(
    IPostingReferenceRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePostingReferenceCommand, CreatePostingReferenceResult>
{
    public async Task<CreatePostingReferenceResult> Handle(
        CreatePostingReferenceCommand request,
        CancellationToken cancellationToken)
    {
        var existing = await repository.GetBySourceAsync(request.SourceType, request.SourceId, request.CompanyId);
        if (existing is not null)
            throw new InvalidOperationException($"Posting reference for source '{request.SourceType}' with ID {request.SourceId} already exists.");

        var reference = new PostingReference(
            request.CompanyId,
            request.JournalEntryId,
            request.SourceType,
            request.SourceId);

        await repository.AddAsync(reference);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePostingReferenceResult(reference.Id);
    }
}
