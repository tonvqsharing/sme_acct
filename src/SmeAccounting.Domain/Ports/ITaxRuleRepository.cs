using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxRuleRepository
{
    Task<TaxRule?> GetByIdAsync(long id);
    Task<TaxRule?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxRule>> GetAllByCompanyAsync(long companyId);
    Task<IReadOnlyList<TaxRule>> GetActiveRulesForDateAsync(DateOnly date, long companyId);
    Task AddAsync(TaxRule taxRule);
}
