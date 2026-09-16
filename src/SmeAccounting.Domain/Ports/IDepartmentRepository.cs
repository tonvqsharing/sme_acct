using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IDepartmentRepository
{
    Task<Department?> GetByIdAsync(long id);
    Task<Department?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Department>> GetAllAsync();
    Task AddAsync(Department department);
}
