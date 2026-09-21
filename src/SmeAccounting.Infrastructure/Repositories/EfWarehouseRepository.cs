using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfWarehouseRepository : IWarehouseRepository
{
    private readonly SmeAccountingDbContext _context;
    public EfWarehouseRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<Warehouse?> GetByIdAsync(long id) => await _context.Warehouses.FirstOrDefaultAsync(e => e.Id == id);
    public async Task<Warehouse?> GetByCodeAsync(string code, long companyId) => await _context.Warehouses.FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    public async Task<IReadOnlyList<Warehouse>> GetAllByCompanyAsync(long companyId) => await _context.Warehouses.AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync();
    public async Task AddAsync(Warehouse warehouse) => await _context.Warehouses.AddAsync(warehouse);
}
