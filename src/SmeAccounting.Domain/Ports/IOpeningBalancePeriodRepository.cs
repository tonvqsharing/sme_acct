using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IOpeningBalancePeriodRepository
{
    Task<OpeningBalancePeriod?> GetByIdAsync(long id);
    Task<OpeningBalancePeriod?> GetByCompanyAndFiscalPeriodAsync(long companyId, long fiscalPeriodId);
    Task<IReadOnlyList<OpeningBalancePeriod>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(OpeningBalancePeriod period);
}
