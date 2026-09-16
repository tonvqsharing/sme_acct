using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfJournalEntryRepository : IJournalEntryRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfJournalEntryRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<JournalEntry?> GetByIdAsync(long id)
    {
        return await _context.JournalEntries
            .Include(e => e.Lines)
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<JournalEntry>> GetAllAsync()
    {
        return await _context.JournalEntries
            .AsNoTracking()
            .OrderByDescending(e => e.Date)
            .ToListAsync();
    }

    public async Task AddAsync(JournalEntry entry)
    {
        await _context.JournalEntries.AddAsync(entry);
    }
}
