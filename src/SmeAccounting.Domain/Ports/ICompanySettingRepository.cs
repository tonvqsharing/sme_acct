using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICompanySettingRepository
{
    Task<CompanySetting?> GetByIdAsync(long id);
    Task<CompanySetting?> GetByCompanyIdAsync(long companyId);
    Task AddAsync(CompanySetting companySetting);
}
