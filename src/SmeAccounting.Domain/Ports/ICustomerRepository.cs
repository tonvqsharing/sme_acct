using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ICustomerRepository
{
    Task<Customer?> GetByIdAsync(long id);
    Task<Customer?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Customer>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Customer customer);
}
