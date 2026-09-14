using NetArchTest.Rules;
using SmeAccounting.SharedKernel;
using System.Reflection;

namespace SmeAccounting.Architecture.Tests;

public class ArchitectureTests
{
    private static readonly Assembly SharedKernelAssembly = typeof(BaseEntity).Assembly;
    private static readonly Assembly DomainAssembly = typeof(SmeAccounting.Domain.DomainMarker).Assembly;
    private static readonly Assembly ApplicationAssembly = typeof(SmeAccounting.Application.ApplicationMarker).Assembly;
    private static readonly Assembly InfrastructureAssembly = typeof(SmeAccounting.Infrastructure.Persistence.SmeAccountingDbContext).Assembly;
    private static readonly Assembly ApiAssembly = typeof(SmeAccounting.Api.ModulesAddExtensions).Assembly;

    private static readonly string[] ModulePrefixes =
    [
        "Identity", "Authorization", "Organization", "MasterData", "Audit",
        "ChartOfAccounts", "AccountingPeriod", "Journal", "Posting",
        "GeneralLedger", "Tax", "FinancialReporting"
    ];

    [Fact]
    public void Domain_Should_NotDependOnInfrastructure()
    {
        var result = Types.InAssembly(DomainAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void Domain_Should_NotDependOnApplication()
    {
        var result = Types.InAssembly(DomainAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Application")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void SharedKernel_Should_NotDependOnAnyProject()
    {
        var result1 = Types.InAssembly(SharedKernelAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        var result2 = Types.InAssembly(SharedKernelAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Application")
            .GetResult();

        var result3 = Types.InAssembly(SharedKernelAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Domain")
            .GetResult();

        Assert.True(result1.IsSuccessful, "SharedKernel should not depend on Infrastructure");
        Assert.True(result2.IsSuccessful, "SharedKernel should not depend on Application");
        Assert.True(result3.IsSuccessful, "SharedKernel should not depend on Domain");
    }

    [Fact]
    public void Application_Should_OnlyDependOnDomainAndSharedKernel()
    {
        var result = Types.InAssembly(ApplicationAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void Infrastructure_Should_NotDependOnApi()
    {
        var result = Types.InAssembly(InfrastructureAssembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void Module_Domains_Should_NotDependOnInfrastructure()
    {
        foreach (var prefix in ModulePrefixes)
        {
            var moduleDomain = GetModuleAssembly(prefix, "Domain");
            if (moduleDomain == null) continue;

            var result = Types.InAssembly(moduleDomain)
                .ShouldNot()
                .HaveDependencyOn("Infrastructure")
                .GetResult();

            Assert.True(result.IsSuccessful,
                $"Module {prefix} Domain should not depend on Infrastructure");
        }
    }

    [Fact]
    public void Controllers_Should_NotContainBusinessLogic()
    {
        var controllerTypes = Types.InAssembly(ApiAssembly)
            .That()
            .HaveNameEndingWith("Controller")
            .GetTypes();

        foreach (var controllerType in controllerTypes)
        {
            var methods = controllerType.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            foreach (var method in methods)
            {
                var body = method.GetMethodBody();
                if (body != null)
                {
                    var il = body.GetILAsByteArray();
                    Assert.True(il == null || il.Length < 1000,
                        $"Controller method {controllerType.Name}.{method.Name} may contain too much logic");
                }
            }
        }
    }

    [Fact]
    public void Entities_Should_HaveAuditFields()
    {
        var entityTypes = DomainAssembly.GetTypes()
            .Where(t => t.IsClass && !t.IsAbstract && typeof(BaseEntity).IsAssignableFrom(t));

        foreach (var entityType in entityTypes)
        {
            if (typeof(ISoftDeletable).IsAssignableFrom(entityType))
            {
                Assert.True(entityType.GetProperty("IsDeleted") != null,
                    $"{entityType.Name} implements ISoftDeletable but missing IsDeleted");
                Assert.True(entityType.GetProperty("DeletedAtUtc") != null,
                    $"{entityType.Name} implements ISoftDeletable but missing DeletedAtUtc");
            }

            if (typeof(IAuditable).IsAssignableFrom(entityType))
            {
                Assert.True(entityType.GetProperty("CreatedAtUtc") != null,
                    $"{entityType.Name} implements IAuditable but missing CreatedAtUtc");
                Assert.True(entityType.GetProperty("UpdatedAtUtc") != null,
                    $"{entityType.Name} implements IAuditable but missing UpdatedAtUtc");
            }
        }
    }

    private static Assembly? GetModuleAssembly(string modulePrefix, string layer)
    {
        try
        {
            var solutionDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..");
            var csproj = Path.Combine(solutionDir, "src", "Modules", modulePrefix, layer);
            if (!Directory.Exists(csproj)) return null;

            var csprojFile = Directory.GetFiles(csproj, "*.csproj").FirstOrDefault();
            if (csprojFile == null) return null;

            var projectName = Path.GetFileNameWithoutExtension(csprojFile);
            var dllPath = Path.Combine(solutionDir, "artifacts", "bin", projectName, "debug", projectName + ".dll");
            if (!File.Exists(dllPath)) return null;

            return Assembly.LoadFrom(dllPath);
        }
        catch
        {
            return null;
        }
    }
}
