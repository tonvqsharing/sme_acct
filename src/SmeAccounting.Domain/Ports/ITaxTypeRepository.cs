using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxTypeRepository
{
    Task<TaxType?> GetByIdAsync(long id);
    Task<TaxType?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxType>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(TaxType taxType);
}
