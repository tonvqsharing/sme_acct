using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxPeriodRepository
{
    Task<TaxPeriod?> GetByIdAsync(long id);
    Task<IReadOnlyList<TaxPeriod>> GetAllByCompanyAsync(long companyId);
    Task<TaxPeriod?> GetByFiscalPeriodAndTaxTypeAsync(long fiscalPeriodId, long taxTypeId, long companyId);
    Task AddAsync(TaxPeriod taxPeriod);
}
