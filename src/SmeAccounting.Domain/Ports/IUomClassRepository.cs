using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IUomClassRepository
{
    Task<UomClass?> GetByIdAsync(long id);
    Task<UomClass?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<UomClass>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(UomClass uomClass);
}