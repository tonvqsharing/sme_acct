using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICompanyRepository
{
    Task<Company?> GetByIdAsync(long id);
    Task<Company?> GetByTaxCodeAsync(string taxCode);
    Task<IReadOnlyList<Company>> GetAllAsync();
    Task AddAsync(Company company);
}
