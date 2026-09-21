using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IUomRepository
{
    Task<Uom?> GetByIdAsync(long id);
    Task<Uom?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<Uom>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(Uom uom);
}
