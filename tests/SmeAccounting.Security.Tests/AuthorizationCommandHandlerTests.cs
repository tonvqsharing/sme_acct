using NSubstitute;
using SmeAccounting.Modules.Authorization.Application.Abstractions;
using SmeAccounting.Modules.Authorization.Application.Commands;
using SmeAccounting.Modules.Authorization.Application.Queries;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Security.Tests;

public class AuthorizationCommandHandlerTests
{
    private static readonly Guid UserId = new("22222222-2222-2222-2222-222222222222");

    [Fact]
    public async Task CreateRole_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.CreateAsync("Admin", null, Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new CreateRoleCommandHandler(roles);

        var result = await handler.Handle(new CreateRoleCommand("Admin", null), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).CreateAsync("Admin", null, Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task CreateRole_Failure_PassesThrough()
    {
        var roles = Substitute.For<IRoleService>();
        roles.CreateAsync(Arg.Any<string>(), Arg.Any<string?>(), Arg.Any<CancellationToken>())
            .Returns(Result.Fail("Authorization.RoleAlreadyExists", "exists"));
        var handler = new CreateRoleCommandHandler(roles);

        var result = await handler.Handle(new CreateRoleCommand("Admin", null), CancellationToken.None);

        Assert.True(result.IsFailure);
        Assert.Contains(result.Failures, f => f.Code == "Authorization.RoleAlreadyExists");
    }

    [Fact]
    public async Task DeleteRole_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.DeleteAsync("Viewer", Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new DeleteRoleCommandHandler(roles);

        var result = await handler.Handle(new DeleteRoleCommand("Viewer"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).DeleteAsync("Viewer", Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task AssignPermission_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.AssignPermissionAsync("Accountant", "accounts.view", Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new AssignPermissionToRoleCommandHandler(roles);

        var result = await handler.Handle(new AssignPermissionToRoleCommand("Accountant", "accounts.view"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).AssignPermissionAsync("Accountant", "accounts.view", Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task RevokePermission_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.RevokePermissionAsync("Accountant", "accounts.view", Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new RevokePermissionFromRoleCommandHandler(roles);

        var result = await handler.Handle(new RevokePermissionFromRoleCommand("Accountant", "accounts.view"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).RevokePermissionAsync("Accountant", "accounts.view", Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task AssignRoleToUser_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.AssignRoleToUserAsync(UserId, "Admin", Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new AssignRoleToUserCommandHandler(roles);

        var result = await handler.Handle(new AssignRoleToUserCommand(UserId, "Admin"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).AssignRoleToUserAsync(UserId, "Admin", Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task RemoveRoleFromUser_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        roles.RemoveRoleFromUserAsync(UserId, "Admin", Arg.Any<CancellationToken>()).Returns(Result.Success());
        var handler = new RemoveRoleFromUserCommandHandler(roles);

        var result = await handler.Handle(new RemoveRoleFromUserCommand(UserId, "Admin"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        await roles.Received(1).RemoveRoleFromUserAsync(UserId, "Admin", Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task ListRoles_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        IReadOnlyList<string> expected = ["Admin", "Viewer"];
        roles.ListRolesAsync(Arg.Any<CancellationToken>()).Returns(Result<IReadOnlyList<string>>.Create(expected));
        var handler = new ListRolesQueryHandler(roles);

        var result = await handler.Handle(new ListRolesQuery(), CancellationToken.None);

        Assert.True(result.IsSuccess);
        Assert.Equal(expected, result.Value);
    }

    [Fact]
    public async Task GetRolePermissions_DelegatesToRoleService()
    {
        var roles = Substitute.For<IRoleService>();
        IReadOnlyList<string> expected = ["accounts.view"];
        roles.GetRolePermissionsAsync("Viewer", Arg.Any<CancellationToken>()).Returns(Result<IReadOnlyList<string>>.Create(expected));
        var handler = new GetRolePermissionsQueryHandler(roles);

        var result = await handler.Handle(new GetRolePermissionsQuery("Viewer"), CancellationToken.None);

        Assert.True(result.IsSuccess);
        Assert.Equal(expected, result.Value);
    }

    [Fact]
    public async Task GetUserPermissions_WrapsPermissionServiceList()
    {
        var permissions = Substitute.For<IPermissionService>();
        IReadOnlyList<string> expected = ["accounts.view", "journal.view"];
        permissions.GetPermissionsAsync(UserId, Arg.Any<CancellationToken>()).Returns(expected);
        var handler = new GetUserPermissionsQueryHandler(permissions);

        var result = await handler.Handle(new GetUserPermissionsQuery(UserId), CancellationToken.None);

        Assert.True(result.IsSuccess);
        Assert.Equal(expected, result.Value);
    }
}
