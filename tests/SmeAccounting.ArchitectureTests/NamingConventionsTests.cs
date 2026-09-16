using NetArchTest.Rules;
using FluentValidation;
using SmeAccounting.Api.Controllers;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.ArchitectureTests;

public class NamingConventionsTests
{
    [Fact]
    public void Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace()
    {
        var result = Types
            .InAssembly(typeof(Account).Assembly)
            .That()
            .AreClasses()
            .And().Inherit(typeof(BaseEntity))
            .Should()
            .ResideInNamespace("SmeAccounting.Domain.Entities")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Entities inheriting BaseEntity must reside in SmeAccounting.Domain.Entities. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Repository_Interfaces_Should_Start_With_I()
    {
        var result = Types
            .InAssembly(typeof(IAccountRepository).Assembly)
            .That()
            .AreInterfaces()
            .And().HaveNameEndingWith("Repository")
            .Should()
            .HaveNameStartingWith("I")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Repository interfaces must start with 'I'. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Commands_In_Commands_Namespace_Should_End_With_Command()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Application.Commands")
            .And().ImplementInterface(typeof(MediatR.IRequest<>))
            .Should()
            .HaveNameEndingWith("Command")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"IRequest types in Commands namespace must end with 'Command'. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Queries_In_Queries_Namespace_Should_End_With_Query()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Application.Queries")
            .And().AreClasses()
            .Should()
            .HaveNameEndingWith("Query")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Types in Queries namespace must end with 'Query'. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void DTOs_Should_End_With_Dto()
    {
        var result = Types
            .InAssembly(typeof(CreateAccountCommand).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Application.DTOs")
            .And().HaveNameEndingWith("Dto")
            .Should()
            .HaveNameEndingWith("Dto")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"DTOs must end with 'Dto'. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }

    [Fact]
    public void Controllers_Should_End_With_Controller()
    {
        var result = Types
            .InAssembly(typeof(HomeController).Assembly)
            .That()
            .ResideInNamespace("SmeAccounting.Api.Controllers")
            .And().AreClasses()
            .Should()
            .HaveNameEndingWith("Controller")
            .GetResult();

        Assert.True(result.IsSuccessful,
            $"Controllers must end with 'Controller'. Violating types: {string.Join(", ", result.FailingTypes?.Select(t => t.FullName) ?? [])}");
    }
}
