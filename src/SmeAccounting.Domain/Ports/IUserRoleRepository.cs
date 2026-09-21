using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IUserRoleRepository
{
    Task AddAsync(UserRole userRole);
}
