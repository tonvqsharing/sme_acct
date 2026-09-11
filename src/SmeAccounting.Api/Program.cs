using SmeAccounting.Api;
using SmeAccounting.Application;
using SmeAccounting.Infrastructure;
using SmeAccounting.Modules.AccountingPeriod.Infrastructure;
using SmeAccounting.Modules.Audit.Infrastructure;
using SmeAccounting.Modules.Authorization.Infrastructure;
using SmeAccounting.Modules.ChartOfAccounts.Infrastructure;
using SmeAccounting.Modules.FinancialReporting.Infrastructure;
using SmeAccounting.Modules.GeneralLedger.Infrastructure;
using SmeAccounting.Modules.Identity.Infrastructure;
using SmeAccounting.Modules.Journal.Infrastructure;
using SmeAccounting.Modules.MasterData.Infrastructure;
using SmeAccounting.Modules.Organization.Infrastructure;
using SmeAccounting.Modules.Posting.Infrastructure;
using SmeAccounting.Modules.Tax.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllersWithViews();
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);
builder.Services.AddModules(
[
    new IdentityModule(),
    new AuthorizationModule(),
    new OrganizationModule(),
    new MasterDataModule(),
    new AuditModule(),
    new ChartOfAccountsModule(),
    new AccountingPeriodModule(),
    new JournalModule(),
    new PostingModule(),
    new GeneralLedgerModule(),
    new TaxModule(),
    new FinancialReportingModule(),
]);

var app = builder.Build();

app.MapStaticAssets();
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}").WithStaticAssets();

app.UseAuthorization();

app.Run();