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

internal sealed class FakeCustomerGroupRepository : ICustomerGroupRepository
{
    private readonly List<CustomerGroup> _items = new();

    public Task<CustomerGroup?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<CustomerGroup?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<CustomerGroup>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<CustomerGroup>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(CustomerGroup customerGroup)
    {
        _items.Add(customerGroup);
        return Task.CompletedTask;
    }

    public IReadOnlyList<CustomerGroup> Stored => _items;
}

internal sealed class FakeSupplierGroupRepository : ISupplierGroupRepository
{
    private readonly List<SupplierGroup> _items = new();

    public Task<SupplierGroup?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<SupplierGroup?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<SupplierGroup>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<SupplierGroup>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(SupplierGroup supplierGroup)
    {
        _items.Add(supplierGroup);
        return Task.CompletedTask;
    }

    public IReadOnlyList<SupplierGroup> Stored => _items;
}

internal sealed class FakeSupplierItemRepository : ISupplierItemRepository
{
    private readonly List<SupplierItem> _items = new();

    public Task<SupplierItem?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<IReadOnlyList<SupplierItem>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<SupplierItem>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(SupplierItem supplierItem)
    {
        _items.Add(supplierItem);
        return Task.CompletedTask;
    }

    public IReadOnlyList<SupplierItem> Stored => _items;
}

internal sealed class FakeUomClassRepository : IUomClassRepository
{
    private readonly List<UomClass> _items = new();

    public Task<UomClass?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<UomClass?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<UomClass>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<UomClass>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(UomClass uomClass)
    {
        _items.Add(uomClass);
        return Task.CompletedTask;
    }

    public IReadOnlyList<UomClass> Stored => _items;
}

internal sealed class FakeUomRepository : IUomRepository
{
    private readonly List<Uom> _items = new();

    public Task<Uom?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<Uom?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<Uom>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<Uom>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(Uom uom)
    {
        _items.Add(uom);
        return Task.CompletedTask;
    }

    public IReadOnlyList<Uom> Stored => _items;
}

internal sealed class FakeUomConversionRepository : IUomConversionRepository
{
    private readonly List<UomConversion> _items = new();

    public Task<UomConversion?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<IReadOnlyList<UomConversion>> GetByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<UomConversion>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(UomConversion conversion)
    {
        _items.Add(conversion);
        return Task.CompletedTask;
    }

    public IReadOnlyList<UomConversion> Stored => _items;
}

internal sealed class FakeItemBarcodeRepository : IItemBarcodeRepository
{
    private readonly List<ItemBarcode> _items = new();

    public Task<ItemBarcode?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<IReadOnlyList<ItemBarcode>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<ItemBarcode>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(ItemBarcode itemBarcode)
    {
        _items.Add(itemBarcode);
        return Task.CompletedTask;
    }

    public IReadOnlyList<ItemBarcode> Stored => _items;
}

internal sealed class FakeItemGroupRepository : IItemGroupRepository
{
    private readonly List<ItemGroup> _items = new();

    public Task<ItemGroup?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<ItemGroup?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<ItemGroup>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<ItemGroup>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(ItemGroup itemGroup)
    {
        _items.Add(itemGroup);
        return Task.CompletedTask;
    }

    public IReadOnlyList<ItemGroup> Stored => _items;
}

internal sealed class FakeItemRepository : IItemRepository
{
    private readonly List<Item> _items = new();

    public Task<Item?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<Item?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<Item>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<Item>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(Item item)
    {
        _items.Add(item);
        return Task.CompletedTask;
    }

    public IReadOnlyList<Item> Stored => _items;
}

internal sealed class FakePriceListRepository : IPriceListRepository
{
    private readonly List<PriceList> _items = new();

    public Task<PriceList?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<PriceList?> GetByCodeAsync(string code, long companyId)
        => Task.FromResult(_items.FirstOrDefault(x => x.Code == code && x.CompanyId == companyId));

    public Task<IReadOnlyList<PriceList>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<PriceList>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(PriceList priceList)
    {
        _items.Add(priceList);
        return Task.CompletedTask;
    }

    public IReadOnlyList<PriceList> Stored => _items;
}

internal sealed class FakeItemPriceListRepository : IItemPriceListRepository
{
    private readonly List<ItemPriceList> _items = new();

    public Task<ItemPriceList?> GetByIdAsync(long id)
        => Task.FromResult(_items.FirstOrDefault(x => x.Id == id));

    public Task<IReadOnlyList<ItemPriceList>> GetAllByCompanyAsync(long companyId)
        => Task.FromResult<IReadOnlyList<ItemPriceList>>(_items.Where(x => x.CompanyId == companyId).ToList());

    public Task AddAsync(ItemPriceList itemPriceList)
    {
        _items.Add(itemPriceList);
        return Task.CompletedTask;
    }

    public IReadOnlyList<ItemPriceList> Stored => _items;
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

internal sealed class FakeClock : IClock
{
    public DateTimeOffset Now { get; set; }
}
