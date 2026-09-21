using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IRoleRepository
{
    Task<Role?> GetByIdAsync(long id);
    Task<Role?> GetByCompanyAndCodeAsync(long companyId, string code);
    Task<IReadOnlyList<Role>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Role role);
}
