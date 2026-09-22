using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPostingReferenceRepository : IPostingReferenceRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPostingReferenceRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PostingReference?> GetByIdAsync(long id)
    {
        return await _context.PostingReferences
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<PostingReference?> GetBySourceAsync(string sourceType, long sourceId, long companyId)
    {
        return await _context.PostingReferences
            .FirstOrDefaultAsync(e => e.SourceType == sourceType && e.SourceId == sourceId && e.CompanyId == companyId);
    }

    public async Task AddAsync(PostingReference reference)
    {
        await _context.PostingReferences.AddAsync(reference);
    }
}
