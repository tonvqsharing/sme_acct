using SmeAccounting.Modules.Authorization.Application.Commands;
using SmeAccounting.Modules.Authorization.Application.Validators;

namespace SmeAccounting.Security.Tests;

public class AuthorizationValidatorTests
{
    private static readonly Guid ValidUserId = new("11111111-1111-1111-1111-111111111111");

    [Fact]
    public async Task CreateRole_ValidName_Passes()
    {
        var validator = new CreateRoleCommandValidator();

        var result = await validator.ValidateAsync(new CreateRoleCommand("Admin", null));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task CreateRole_InvalidNames_Fail()
    {
        var validator = new CreateRoleCommandValidator();
        var badNames = new[] { string.Empty, "bad name!", "role/slash", new string('a', 257) };

        foreach (var name in badNames)
        {
            var result = await validator.ValidateAsync(new CreateRoleCommand(name, null));
            Assert.False(result.IsValid);
        }
    }

    [Fact]
    public async Task DeleteRole_ValidName_Passes()
    {
        var validator = new DeleteRoleCommandValidator();

        var result = await validator.ValidateAsync(new DeleteRoleCommand("Viewer"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task DeleteRole_EmptyName_Fails()
    {
        var validator = new DeleteRoleCommandValidator();

        var result = await validator.ValidateAsync(new DeleteRoleCommand(string.Empty));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task AssignPermission_KnownPermission_Passes()
    {
        var validator = new AssignPermissionToRoleCommandValidator();

        var result = await validator.ValidateAsync(new AssignPermissionToRoleCommand("Accountant", "accounts.view"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task AssignPermission_UnknownPermission_Fails()
    {
        var validator = new AssignPermissionToRoleCommandValidator();

        var result = await validator.ValidateAsync(new AssignPermissionToRoleCommand("Accountant", "nope.unknown"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task RevokePermission_UnknownPermission_Fails()
    {
        var validator = new RevokePermissionFromRoleCommandValidator();

        var result = await validator.ValidateAsync(new RevokePermissionFromRoleCommand("Accountant", "nope.unknown"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task RevokePermission_KnownPermission_Passes()
    {
        var validator = new RevokePermissionFromRoleCommandValidator();

        var result = await validator.ValidateAsync(new RevokePermissionFromRoleCommand("Accountant", "journal.post"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task AssignRoleToUser_ValidInput_Passes()
    {
        var validator = new AssignRoleToUserCommandValidator();

        var result = await validator.ValidateAsync(new AssignRoleToUserCommand(ValidUserId, "Admin"));

        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task AssignRoleToUser_EmptyUserId_Fails()
    {
        var validator = new AssignRoleToUserCommandValidator();

        var result = await validator.ValidateAsync(new AssignRoleToUserCommand(Guid.Empty, "Admin"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task RemoveRoleFromUser_EmptyUserId_Fails()
    {
        var validator = new RemoveRoleFromUserCommandValidator();

        var result = await validator.ValidateAsync(new RemoveRoleFromUserCommand(Guid.Empty, "Admin"));

        Assert.False(result.IsValid);
    }

    [Fact]
    public async Task RemoveRoleFromUser_ValidInput_Passes()
    {
        var validator = new RemoveRoleFromUserCommandValidator();

        var result = await validator.ValidateAsync(new RemoveRoleFromUserCommand(ValidUserId, "Admin"));

        Assert.True(result.IsValid);
    }
}
