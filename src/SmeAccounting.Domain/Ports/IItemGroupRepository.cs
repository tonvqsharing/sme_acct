using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IItemGroupRepository
{
    Task<ItemGroup?> GetByIdAsync(long id);
    Task<ItemGroup?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<ItemGroup>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(ItemGroup itemGroup);
}