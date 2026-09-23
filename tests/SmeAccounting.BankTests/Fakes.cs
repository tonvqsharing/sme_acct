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

internal sealed class FakeJournalEntryRepository : IJournalEntryRepository
{
    private readonly List<JournalEntry> _items = new();
    private long _nextId = 1;

    public Task<JournalEntry?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<IReadOnlyList<JournalEntry>> GetAllAsync()
        => Task.FromResult<IReadOnlyList<JournalEntry>>(_items.ToList());

    public Task AddAsync(JournalEntry entry)
    {
        entry.Id = _nextId++;
        _items.Add(entry);
        return Task.CompletedTask;
    }

    public IReadOnlyList<JournalEntry> Stored => _items;
}

internal sealed class FakeOpeningBalancePeriodRepository : IOpeningBalancePeriodRepository
{
    private readonly List<OpeningBalancePeriod> _items = new();

    public Task<OpeningBalancePeriod?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<OpeningBalancePeriod?> GetByCompanyAndFiscalPeriodAsync(long companyId, long fiscalPeriodId)
        => Task.FromResult(_items.FirstOrDefault(x => x.CompanyId == companyId && x.FiscalPeriodId == fiscalPeriodId));

    public Task<IReadOnlyList<OpeningBalancePeriod>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<OpeningBalancePeriod>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(OpeningBalancePeriod period)
    {
        _items.Add(period);
        return Task.CompletedTask;
    }

    public IReadOnlyList<OpeningBalancePeriod> Stored => _items;
}

internal sealed class FakeVoucherTypeRepository : IVoucherTypeRepository
{
    private readonly List<VoucherType> _items = new();
    private long _nextId = 1;

    public Task<VoucherType?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<VoucherType?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<VoucherType>> GetAllAsync()
        => Task.FromResult<IReadOnlyList<VoucherType>>(_items.ToList());

    public Task AddAsync(VoucherType voucherType)
    {
        voucherType.Id = _nextId++;
        _items.Add(voucherType);
        return Task.CompletedTask;
    }

    public IReadOnlyList<VoucherType> Stored => _items;
}

internal sealed class FakeDocumentNumberingSeriesRepository : IDocumentNumberingSeriesRepository
{
    private readonly List<DocumentNumberingSeries> _items = new();

    public Task<DocumentNumberingSeries?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.VoucherTypeId == voucherTypeId && x.CompanyId == companyId && x.IsDefault));

    public Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<DocumentNumberingSeries>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(DocumentNumberingSeries series)
    {
        _items.Add(series);
        return Task.CompletedTask;
    }

    public IReadOnlyList<DocumentNumberingSeries> Stored => _items;
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
