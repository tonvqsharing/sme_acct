using System.Xml.Linq;
using NetArchTest.Rules;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.ArchitectureTests;

public class DomainPurityTests
{
    private static string GetDomainCsprojPath()
    {
        var testAssemblyDir = Path.GetDirectoryName(typeof(DomainPurityTests).Assembly.Location)!;
        return Path.GetFullPath(Path.Combine(
            testAssemblyDir, "..", "..", "..", "..", "..",
            "src", "SmeAccounting.Domain", "SmeAccounting.Domain.csproj"));
    }

    [Fact]
    public void Domain_Should_Have_No_NuGet_PackageReferences()
    {
        var csprojPath = GetDomainCsprojPath();
        Assert.True(File.Exists(csprojPath), $"Domain csproj not found at: {csprojPath}");

        var doc = XDocument.Load(csprojPath);
        var packageRefs = doc.Descendants("PackageReference").ToList();

        Assert.Empty(packageRefs);
    }

    [Fact]
    public void Domain_Should_Not_Reference_Microsoft_Or_Npgsql_Packages()
    {
        var csprojPath = GetDomainCsprojPath();
        Assert.True(File.Exists(csprojPath), $"Domain csproj not found at: {csprojPath}");

        var doc = XDocument.Load(csprojPath);
        var forbiddenPrefixes = new[] { "Microsoft.", "Npgsql.", "Serilog.", "EFCore." };

        var violations = doc.Descendants("PackageReference")
            .Select(x => (string?)x.Attribute("Include") ?? "")
            .Where(pkg => forbiddenPrefixes.Any(pfx => pkg.StartsWith(pfx, StringComparison.OrdinalIgnoreCase)))
            .ToList();

        Assert.Empty(violations);
    }

    [Fact]
    public void Domain_Should_Have_No_EntityFramework_Assembly_Dependency()
    {
        var result = Types
            .InAssembly(typeof(Account).Assembly)
            .ShouldNot()
            .HaveDependencyOn("Microsoft.EntityFrameworkCore")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Domain must not depend on Microsoft.EntityFrameworkCore. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }
}
