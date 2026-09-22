using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPostingReferenceRepository
{
    Task<PostingReference?> GetByIdAsync(long id);
    Task<PostingReference?> GetBySourceAsync(string sourceType, long sourceId, long companyId);
    Task AddAsync(PostingReference reference);
}
