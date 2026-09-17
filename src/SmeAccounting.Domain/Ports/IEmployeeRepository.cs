using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IEmployeeRepository
{
    Task<Employee?> GetByIdAsync(long id);
    Task<Employee?> GetByCodeAsync(string code, long companyId);
    Task<Employee?> GetByEmployeeNumberAsync(string employeeNumber, long companyId);
    Task<IReadOnlyList<Employee>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Employee employee);
}
