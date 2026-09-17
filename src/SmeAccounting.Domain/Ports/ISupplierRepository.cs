using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ISupplierRepository
{
    Task<Supplier?> GetByIdAsync(long id);
    Task<Supplier?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Supplier>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Supplier supplier);
}
