using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPostingService
{
    Task PostAsync(JournalEntry entry);
}
