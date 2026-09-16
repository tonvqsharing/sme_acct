using NetArchTest.Rules;
using SmeAccounting.Api.Controllers;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.ArchitectureTests;

public class LayerCouplingTests
{
    [Fact]
    public void Controllers_Should_Not_Reference_Domain_Entities_Namespace()
    {
        var result = Types
            .InAssembly(typeof(HomeController).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Api.Controllers")
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Domain.Entities")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Controllers must not reference Domain.Entities namespace. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Controllers_Should_Not_Reference_Domain_Ports_Namespace()
    {
        var result = Types
            .InAssembly(typeof(HomeController).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Api.Controllers")
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Domain.Ports")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Controllers must not reference Domain.Ports namespace. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Application_Handlers_Should_Not_Reference_Infrastructure_Namespace()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .That()
            .ImplementInterface(typeof(MediatR.IRequestHandler<,>))
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Infrastructure")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Application handlers must not reference Infrastructure namespace. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Infrastructure_Should_Not_Reference_Api_Namespace()
    {
        var result = Types
            .InAssembly(typeof(SmeAccountingDbContext).Assembly)
            .ShouldNot()
            .HaveDependencyOn("SmeAccounting.Api")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Infrastructure must not reference Api namespace. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }
}
