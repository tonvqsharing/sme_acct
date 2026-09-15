using MediatR;
using Microsoft.AspNetCore.Mvc;
using NSubstitute;
using SmeAccounting.Api.Controllers;
using SmeAccounting.Modules.Authorization.Application.Commands;
using SmeAccounting.Modules.Authorization.Application.Queries;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Security.Tests;

public class RolesControllerTests
{
    private static readonly Guid UserId = new("33333333-3333-3333-3333-333333333333");

    [Fact]
    public async Task Index_Success_ReturnsOkWithRoles()
    {
        var mediator = Substitute.For<IMediator>();
        IReadOnlyList<string> roles = ["Admin", "Viewer"];
        mediator.Send(Arg.Any<ListRolesQuery>(), Arg.Any<CancellationToken>())
            .Returns(Result<IReadOnlyList<string>>.Create(roles));
        var controller = new RolesController(mediator);

        var result = await controller.Index(CancellationToken.None);

        var ok = Assert.IsType<OkObjectResult>(result);
        Assert.Equal(roles, ok.Value);
    }

    [Fact]
    public async Task Index_Failure_ReturnsBadRequest()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<ListRolesQuery>(), Arg.Any<CancellationToken>())
            .Returns(Result<IReadOnlyList<string>>.Fail("Authorization.RoleNotFound", "missing"));
        var controller = new RolesController(mediator);

        var result = await controller.Index(CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task Create_Success_ReturnsOk()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<CreateRoleCommand>(), Arg.Any<CancellationToken>()).Returns(Result.Success());
        var controller = new RolesController(mediator);

        var result = await controller.Create("Admin", null, CancellationToken.None);

        Assert.IsType<OkResult>(result);
    }

    [Fact]
    public async Task Create_Failure_ReturnsBadRequest()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<CreateRoleCommand>(), Arg.Any<CancellationToken>())
            .Returns(Result.Fail("Authorization.RoleAlreadyExists", "exists"));
        var controller = new RolesController(mediator);

        var result = await controller.Create("Admin", null, CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task GrantPermission_Failure_ReturnsBadRequest()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<AssignPermissionToRoleCommand>(), Arg.Any<CancellationToken>())
            .Returns(Result.Fail("Authorization.UnknownPermission", "unknown"));
        var controller = new RolesController(mediator);

        var result = await controller.GrantPermission("Admin", "nope.unknown", CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task AssignUser_Success_ReturnsOk()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<AssignRoleToUserCommand>(), Arg.Any<CancellationToken>()).Returns(Result.Success());
        var controller = new RolesController(mediator);

        var result = await controller.AssignUser(UserId, "Admin", CancellationToken.None);

        Assert.IsType<OkResult>(result);
    }

    [Fact]
    public async Task RemoveUser_Failure_ReturnsBadRequest()
    {
        var mediator = Substitute.For<IMediator>();
        mediator.Send(Arg.Any<RemoveRoleFromUserCommand>(), Arg.Any<CancellationToken>())
            .Returns(Result.Fail("Authorization.UserNotFound", "missing"));
        var controller = new RolesController(mediator);

        var result = await controller.RemoveUser(UserId, "Admin", CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task Permissions_Success_ReturnsOkWithList()
    {
        var mediator = Substitute.For<IMediator>();
        IReadOnlyList<string> permissions = ["accounts.view"];
        mediator.Send(Arg.Any<GetRolePermissionsQuery>(), Arg.Any<CancellationToken>())
            .Returns(Result<IReadOnlyList<string>>.Create(permissions));
        var controller = new RolesController(mediator);

        var result = await controller.Permissions("Viewer", CancellationToken.None);

        var ok = Assert.IsType<OkObjectResult>(result);
        Assert.Equal(permissions, ok.Value);
    }
}
