using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingReferenceByIdHandler(
    IPostingReferenceRepository repository)
    : IRequestHandler<GetPostingReferenceByIdQuery, PostingReferenceDto?>
{
    public async Task<PostingReferenceDto?> Handle(
        GetPostingReferenceByIdQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.PostingReferenceId);
        return entity is null ? null : new PostingReferenceDto(
            entity.Id,
            entity.CompanyId,
            entity.JournalEntryId,
            entity.SourceType,
            entity.SourceId);
    }
}
