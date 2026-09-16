using NetArchTest.Rules;
using SmeAccounting.Api.Controllers;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.ArchitectureTests;

public class DependencyRulesTests
{
    [Fact]
    public void Domain_Should_Not_Depend_On_Application()
    {
        var result = Types
            .InAssembly(typeof(Account).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Application")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Domain must not depend on Application. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Domain_Should_Not_Depend_On_Infrastructure()
    {
        var result = Types
            .InAssembly(typeof(Account).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Domain must not depend on Infrastructure. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Domain_Should_Not_Depend_On_Api()
    {
        var result = Types
            .InAssembly(typeof(Account).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Domain must not depend on Api. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Application_Should_Not_Depend_On_Infrastructure()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Application must not depend on Infrastructure. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Application_Should_Not_Depend_On_Api()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Application must not depend on Api. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Infrastructure_Should_Not_Depend_On_Api()
    {
        var result = Types
            .InAssembly(typeof(SmeAccountingDbContext).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Infrastructure must not depend on Api. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Api_Controllers_Should_Not_Depend_On_Infrastructure()
    {
        var result = Types
            .InAssembly(typeof(HomeController).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Api.Controllers")
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Api controllers must not depend on Infrastructure (only composition root may). Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }
}
