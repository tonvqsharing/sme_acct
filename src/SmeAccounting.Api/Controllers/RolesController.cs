using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Modules.Authorization.Application.Commands;
using SmeAccounting.Modules.Authorization.Application.Queries;
using SmeAccounting.Modules.Authorization.Domain;
using SmeAccounting.SharedKernel;

namespace SmeAccounting.Api.Controllers;

[Authorize(Policy = "Permission:" + Permissions.Users.ManageRoles)]
public class RolesController : Controller
{
    private readonly IMediator _mediator;

    public RolesController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new ListRolesQuery(), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpGet]
    public async Task<IActionResult> Permissions(string roleName, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new GetRolePermissionsQuery(roleName), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> Create(string roleName, string? description, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new CreateRoleCommand(roleName, description), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> Delete(string roleName, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new DeleteRoleCommand(roleName), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> GrantPermission(string roleName, string permission, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new AssignPermissionToRoleCommand(roleName, permission), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> RevokePermission(string roleName, string permission, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new RevokePermissionFromRoleCommand(roleName, permission), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> AssignUser(Guid userId, string roleName, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new AssignRoleToUserCommand(userId, roleName), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    [HttpPost]
    public async Task<IActionResult> RemoveUser(Guid userId, string roleName, CancellationToken cancellationToken)
    {
        var result = await _mediator.Send(new RemoveRoleFromUserCommand(userId, roleName), cancellationToken).ConfigureAwait(false);
        return ToActionResult(result);
    }

    private static IActionResult ToActionResult(Result result)
    {
        return result.IsSuccess ? new OkResult() : new BadRequestObjectResult(result.Failures);
    }

    private static IActionResult ToActionResult<T>(Result<T> result)
    {
        return result.IsSuccess ? new OkObjectResult(result.Value) : new BadRequestObjectResult(result.Failures);
    }
}
