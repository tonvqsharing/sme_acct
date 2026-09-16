using MediatR;

namespace SmeAccounting.Application.Commands;

public record PostJournalEntryCommand(long JournalEntryId) : IRequest<PostJournalEntryResult>;

public record PostJournalEntryResult(long JournalEntryId, DateTimeOffset PostedAt);
