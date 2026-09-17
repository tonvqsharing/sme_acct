using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IOpeningBalanceMappingRepository
{
    Task<OpeningBalanceMapping?> GetByIdAsync(long id);
    Task<IReadOnlyList<OpeningBalanceMapping>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(OpeningBalanceMapping mapping);
}
