using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IJournalEntryRepository
{
    Task<JournalEntry?> GetByIdAsync(long id);
    Task<IReadOnlyList<JournalEntry>> GetAllAsync();
    Task AddAsync(JournalEntry entry);
}
