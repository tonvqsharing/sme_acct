using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Api.ViewModels;

public record JournalEntryViewModel(
    IReadOnlyList<JournalEntryDto> Entries);
