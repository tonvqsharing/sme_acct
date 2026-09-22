using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingReferenceBySourceHandler(
    IPostingReferenceRepository repository)
    : IRequestHandler<GetPostingReferenceBySourceQuery, PostingReferenceDto?>
{
    public async Task<PostingReferenceDto?> Handle(
        GetPostingReferenceBySourceQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetBySourceAsync(request.SourceType, request.SourceId, request.CompanyId);
        return entity is null ? null : new PostingReferenceDto(
            entity.Id,
            entity.CompanyId,
            entity.JournalEntryId,
            entity.SourceType,
            entity.SourceId);
    }
}
