using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPostingConfigurationRepository : IPostingConfigurationRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPostingConfigurationRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PostingConfiguration?> GetByIdAsync(long id)
    {
        return await _context.PostingConfigurations
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<PostingConfiguration>> GetAllByVoucherTypeAsync(
        long voucherTypeId, long companyId)
    {
        return await _context.PostingConfigurations
            .AsNoTracking()
            .Where(e => e.VoucherTypeId == voucherTypeId && e.CompanyId == companyId)
            .OrderBy(e => e.DisplayOrder)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<PostingConfiguration>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.PostingConfigurations
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.DisplayOrder)
            .ToListAsync();
    }

    public async Task AddAsync(PostingConfiguration postingConfiguration)
    {
        await _context.PostingConfigurations.AddAsync(postingConfiguration);
    }
}
