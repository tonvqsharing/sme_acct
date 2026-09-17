using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Infrastructure.Persistence;

public class SmeAccountingDbContext : DbContext, IUnitOfWork
{
    public DbSet<Account> Accounts => Set<Account>();
    public DbSet<AccountGroup> AccountGroups => Set<AccountGroup>();
    public DbSet<JournalEntry> JournalEntries => Set<JournalEntry>();
    public DbSet<JournalEntryLine> JournalEntryLines => Set<JournalEntryLine>();
    public DbSet<FiscalYear> FiscalYears => Set<FiscalYear>();
    public DbSet<FiscalPeriod> FiscalPeriods => Set<FiscalPeriod>();
    public DbSet<PostingReference> PostingReferences => Set<PostingReference>();
    public DbSet<Company> Companies => Set<Company>();
    public DbSet<Currency> Currencies => Set<Currency>();
    public DbSet<ExchangeRate> ExchangeRates => Set<ExchangeRate>();
    public DbSet<Department> Departments => Set<Department>();
    public DbSet<CostCenter> CostCenters => Set<CostCenter>();
    public DbSet<Project> Projects => Set<Project>();
    public DbSet<VoucherType> VoucherTypes => Set<VoucherType>();
    public DbSet<DocumentNumberingSeries> DocumentNumberingSeries => Set<DocumentNumberingSeries>();
    public DbSet<TransactionReason> TransactionReasons => Set<TransactionReason>();
    public DbSet<PostingConfiguration> PostingConfigurations => Set<PostingConfiguration>();
    public DbSet<OpeningBalanceMapping> OpeningBalanceMappings => Set<OpeningBalanceMapping>();
    public DbSet<TaxType> TaxTypes => Set<TaxType>();
    public DbSet<TaxTreatment> TaxTreatments => Set<TaxTreatment>();
    public DbSet<TaxAuthority> TaxAuthorities => Set<TaxAuthority>();
    public DbSet<TaxRate> TaxRates => Set<TaxRate>();
    public DbSet<TaxRule> TaxRules => Set<TaxRule>();
    public DbSet<TaxExemptionReason> TaxExemptionReasons => Set<TaxExemptionReason>();
    public DbSet<TaxAccountingMapping> TaxAccountingMappings => Set<TaxAccountingMapping>();
    public DbSet<TaxPeriod> TaxPeriods => Set<TaxPeriod>();

    public SmeAccountingDbContext(DbContextOptions<SmeAccountingDbContext> options)
        : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Ignore<DomainEvent>();
        modelBuilder.Ignore<AccountCreated>();
        modelBuilder.Ignore<AccountDeprecated>();
        modelBuilder.Ignore<JournalEntryPosted>();
        modelBuilder.Ignore<PeriodClosed>();
        modelBuilder.Ignore<CompanyCreated>();
        modelBuilder.Ignore<CurrencyCreated>();
        modelBuilder.Ignore<FiscalYearCreated>();
        modelBuilder.Ignore<ExchangeRateRecorded>();
        modelBuilder.Ignore<DepartmentCreated>();
        modelBuilder.Ignore<CostCenterCreated>();
        modelBuilder.Ignore<ProjectCreated>();
        modelBuilder.Ignore<VoucherTypeCreated>();
        modelBuilder.Ignore<TransactionReasonCreated>();
        modelBuilder.Ignore<TaxTypeCreated>();
        modelBuilder.Ignore<TaxTreatmentCreated>();
        modelBuilder.Ignore<TaxAuthorityCreated>();
        modelBuilder.Ignore<TaxRateCreated>();
        modelBuilder.Ignore<TaxRuleCreated>();
        modelBuilder.Ignore<TaxExemptionReasonCreated>();
        modelBuilder.Ignore<TaxAccountingMappingCreated>();
        modelBuilder.Ignore<TaxPeriodCreated>();
        modelBuilder.Ignore<TaxPeriodClosed>();
        modelBuilder.Ignore<CustomerCreated>();
        modelBuilder.Ignore<SupplierCreated>();
        modelBuilder.Ignore<EmployeeCreated>();
        modelBuilder.Ignore<PaymentTermCreated>();

        modelBuilder.ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly);
        base.OnModelCreating(modelBuilder);
    }

    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        var domainEvents = ChangeTracker.Entries<BaseEntity>()
            .Select(e => e.Entity)
            .SelectMany(e => e.DomainEvents)
            .ToList();

        var result = await base.SaveChangesAsync(cancellationToken);

        foreach (var domainEvent in domainEvents)
        {
            await PublishDomainEventAsync(domainEvent);
        }

        return result;
    }

    private static async Task PublishDomainEventAsync(DomainEvent domainEvent)
    {
        await Task.CompletedTask;
    }
}
