using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITaxAuthorityRepository
{
    Task<TaxAuthority?> GetByIdAsync(long id);
    Task<TaxAuthority?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TaxAuthority>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(TaxAuthority taxAuthority);
}
