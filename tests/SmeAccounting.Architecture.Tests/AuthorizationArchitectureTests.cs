using System.Reflection;
using NetArchTest.Rules;

namespace SmeAccounting.Architecture.Tests;

/// <summary>
/// Authorization module layer rules. Assemblies must actually load —
/// a null assembly silently skips the rule, so load failure is a test
/// failure, not a pass.
/// </summary>
public class AuthorizationArchitectureTests
{
    private static Assembly LoadModuleAssembly(string modulePrefix, string layer)
    {
        var solutionDir = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..");
        var projectName = $"SmeAccounting.Modules.{modulePrefix}.{layer}";
        var layerDir = Path.Combine(solutionDir, "src", "Modules", modulePrefix, layer);

        foreach (var config in new[] { "Debug", "Release", "debug", "release" })
        {
            var dllPath = Path.Combine(solutionDir, "artifacts", "bin", projectName, config, projectName + ".dll");
            if (File.Exists(dllPath))
            {
                return Assembly.LoadFrom(dllPath);
            }
        }

        throw new FileNotFoundException(
            $"Could not load {projectName}. Build the module (Debug or Release) before running architecture tests. Searched under {layerDir}.");
    }

    [Fact]
    public void AuthorizationApplication_Should_NotDependOnInfrastructure()
    {
        var assembly = LoadModuleAssembly("Authorization", "Application");

        var result = Types.InAssembly(assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void AuthorizationApplication_Should_NotDependOnApi()
    {
        var assembly = LoadModuleAssembly("Authorization", "Application");

        var result = Types.InAssembly(assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void AuthorizationInfrastructure_Should_NotDependOnApi()
    {
        var assembly = LoadModuleAssembly("Authorization", "Infrastructure");

        var result = Types.InAssembly(assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }

    [Fact]
    public void AuthorizationDomain_Should_NotDependOnInfrastructure()
    {
        var assembly = LoadModuleAssembly("Authorization", "Domain");

        var result = Types.InAssembly(assembly)
            .ShouldNot()
            .HaveDependencyOn("Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful);
    }
}
