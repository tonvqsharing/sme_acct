using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IVoucherTypeRepository
{
    Task<VoucherType?> GetByIdAsync(long id);
    Task<VoucherType?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<VoucherType>> GetAllAsync();
    Task AddAsync(VoucherType voucherType);
}
