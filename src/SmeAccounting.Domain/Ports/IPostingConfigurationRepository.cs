using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPostingConfigurationRepository
{
    Task<PostingConfiguration?> GetByIdAsync(long id);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByVoucherTypeAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PostingConfiguration postingConfiguration);
}
