using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetJournalEntryQuery(long JournalEntryId) : IRequest<JournalEntryDto?>;
