using MediatR;

namespace SmeAccounting.Application.Commands;

public record CreatePostingReferenceCommand(
    long CompanyId,
    long JournalEntryId,
    string SourceType,
    long SourceId) : IRequest<CreatePostingReferenceResult>;

public record CreatePostingReferenceResult(long Id);
