using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IOpeningBalanceEntryRepository
{
    Task<OpeningBalanceEntry?> GetByIdAsync(long id);
    Task<IReadOnlyList<OpeningBalanceEntry>> GetAllByPeriodAsync(long periodId);
    Task<IReadOnlyList<OpeningBalanceEntry>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(OpeningBalanceEntry entry);
}
