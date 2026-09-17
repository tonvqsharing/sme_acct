using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxTreatmentRepository
{
    Task<TaxTreatment?> GetByIdAsync(long id);
    Task<TaxTreatment?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxTreatment>> GetAllByCompanyAsync(long companyId);
    Task<IReadOnlyList<TaxTreatment>> GetAllByTaxTypeAsync(long taxTypeId);
    Task AddAsync(TaxTreatment taxTreatment);
}
