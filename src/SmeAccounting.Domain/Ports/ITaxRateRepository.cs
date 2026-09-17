using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxRateRepository
{
    Task<TaxRate?> GetByIdAsync(long id);
    Task<TaxRate?> GetByTaxTypeAndDateAsync(long taxTypeId, DateOnly date, long companyId);
    Task<IReadOnlyList<TaxRate>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(TaxRate taxRate);
}
