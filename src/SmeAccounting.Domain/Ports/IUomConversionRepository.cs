using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IUomConversionRepository
{
    Task<UomConversion?> GetByIdAsync(long id);
    Task<IReadOnlyList<UomConversion>> GetByCompanyAsync(long companyId);
    Task AddAsync(UomConversion conversion);
}
