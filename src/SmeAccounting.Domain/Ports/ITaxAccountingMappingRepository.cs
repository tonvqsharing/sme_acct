using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxAccountingMappingRepository
{
    Task<TaxAccountingMapping?> GetByIdAsync(long id);
    Task<IReadOnlyList<TaxAccountingMapping>> GetAllByCompanyAsync(long companyId);
    Task<TaxAccountingMapping?> GetByTaxTypeAndTreatmentAsync(long taxTypeId, long taxTreatmentId, long companyId);
    Task AddAsync(TaxAccountingMapping mapping);
}
