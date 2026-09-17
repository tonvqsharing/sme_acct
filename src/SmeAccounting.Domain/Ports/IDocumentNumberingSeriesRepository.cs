using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IDocumentNumberingSeriesRepository
{
    Task<DocumentNumberingSeries?> GetByIdAsync(long id);
    Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(DocumentNumberingSeries series);
}
