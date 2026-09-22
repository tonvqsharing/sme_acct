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

internal sealed class FakePaymentMethodRepository : IPaymentMethodRepository
{
    private readonly List<PaymentMethod> _items = new();

    public Task<PaymentMethod?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<PaymentMethod?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<PaymentMethod>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<PaymentMethod>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(PaymentMethod method)
    {
        _items.Add(method);
        return Task.CompletedTask;
    }

    public IReadOnlyList<PaymentMethod> Stored => _items;
}

internal sealed class FakePostingReferenceRepository : IPostingReferenceRepository
{
    private readonly List<PostingReference> _items = new();

    public Task<PostingReference?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<PostingReference?> GetBySourceAsync(string sourceType, long sourceId, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.SourceType == sourceType && x.SourceId == sourceId && x.CompanyId == companyId));

    public Task AddAsync(PostingReference reference)
    {
        _items.Add(reference);
        return Task.CompletedTask;
    }

    public IReadOnlyList<PostingReference> Stored => _items;
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
