using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.BankTests;

internal sealed class FakeBankRepository : IBankRepository
{
    private readonly List<Bank> _banks = new();

    public Task<Bank?> GetByIdAsync(long id)
        => Task.FromResult(_banks.FirstOrDefault(b => b.Id == id));

    public Task<Bank?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_banks.FirstOrDefault(b => b.Code == code && b.CompanyId == companyId));

    public Task<IReadOnlyList<Bank>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<Bank>>(_banks.Where(b => b.CompanyId == companyId).ToList());

    public Task AddAsync(Bank bank)
    {
        _banks.Add(bank);
        return Task.CompletedTask;
    }

    public IReadOnlyList<Bank> Stored => _banks;
}

internal sealed class FakeUnitOfWork : IUnitOfWork
{
    public int SaveCalledCount { get; private set; }

    public Task<int> SaveChangesAsync(CancellationToken ct = default)
    {
        SaveCalledCount++;
        return Task.FromResult(1);
    }
}
