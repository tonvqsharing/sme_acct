using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfItemBarcodeRepository : IItemBarcodeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfItemBarcodeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<ItemBarcode?> GetByIdAsync(long id)
    {
        return await _context.ItemBarcodes
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<ItemBarcode>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.ItemBarcodes
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.ItemId)
            .ThenBy(e => e.Barcode)
            .ToListAsync();
    }

    public async Task AddAsync(ItemBarcode itemBarcode)
    {
        await _context.ItemBarcodes.AddAsync(itemBarcode);
    }
}