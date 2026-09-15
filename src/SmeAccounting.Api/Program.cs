using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SmeAccounting.Api;
using SmeAccounting.Application;
using SmeAccounting.Infrastructure;
using SmeAccounting.Infrastructure.ErrorHandling;
using SmeAccounting.Infrastructure.ForwardedHeaders;
using SmeAccounting.Infrastructure.Health;
using SmeAccounting.Infrastructure.Localization;
using SmeAccounting.Infrastructure.Persistence;
using SmeAccounting.Modules.AccountingPeriod.Infrastructure;
using SmeAccounting.Modules.Audit.Infrastructure;
using SmeAccounting.Modules.Authorization.Infrastructure;
using SmeAccounting.Modules.ChartOfAccounts.Infrastructure;
using SmeAccounting.Modules.FinancialReporting.Infrastructure;
using SmeAccounting.Modules.GeneralLedger.Infrastructure;
using SmeAccounting.Modules.Authorization.Infrastructure.Seeding;
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
builder.Services.AddIdentityModule(builder.Configuration);
builder.Services.AddAuthorizationModule();
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

app.UseForwardedHeaders();
app.UseRequestLocalization();
app.UseGlobalExceptionHandler();
app.UseRouting();
app.UseHealthInfrastructure();

// Fail fast if model/migrations out of sync, then ensure Identity schema + seed roles/users
if (!app.Environment.IsEnvironment("Testing"))
{
    using (var scope = app.Services.CreateScope())
    {
        var db = scope.ServiceProvider.GetRequiredService<SmeAccountingDbContext>();
        if (db.Database.GetPendingMigrations().Any())
        {
            throw new InvalidOperationException("Pending migrations detected. Apply migrations before starting the application.");
        }

        var identityDb = scope.ServiceProvider.GetRequiredService<IdentityDbContext>();
        await identityDb.Database.EnsureCreatedAsync();

        var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<ApplicationRole>>();
        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<ApplicationUser>>();
        var logger = scope.ServiceProvider.GetRequiredService<ILoggerFactory>().CreateLogger("StartupSeed");
        var adminPassword = Environment.GetEnvironmentVariable("ADMIN_PASSWORD");

        await RoleSeeder.SeedAsync(roleManager, logger);
        await UserSeeder.SeedAsync(userManager, roleManager, logger, adminPassword);
        await AuthorizationRoleSeeder.SeedAsync(roleManager, userManager, logger);
    }
}

app.MapStaticAssets();
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}").WithStaticAssets();

app.UseAuthentication();
app.UseAuthorization();

app.Run();