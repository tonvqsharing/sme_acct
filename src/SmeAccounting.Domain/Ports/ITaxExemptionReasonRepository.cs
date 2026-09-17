using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxExemptionReasonRepository
{
    Task<TaxExemptionReason?> GetByIdAsync(long id);
    Task<TaxExemptionReason?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxExemptionReason>> GetAllByCompanyAsync(long companyId);
    Task<IReadOnlyList<TaxExemptionReason>> GetAllByTaxTypeAsync(long taxTypeId);
    Task AddAsync(TaxExemptionReason taxExemptionReason);
}
