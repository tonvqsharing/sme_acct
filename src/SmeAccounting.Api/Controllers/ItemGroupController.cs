using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ItemGroupController : Controller
{
    private readonly IMediator _mediator;

    public ItemGroupController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var itemGroups = await _mediator.Send(new GetItemGroupsByCompanyQuery(companyId), ct);
        return View(itemGroups);
    }

    [HttpGet]
    public IActionResult Create() => View();

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, string code, string name, string? description, CancellationToken ct)
    {
        try
        {
            var command = new CreateItemGroupCommand(companyId, code, name, description);
            await _mediator.Send(command, ct);
            return RedirectToAction(nameof(Index), new { companyId });
        }
        catch (ValidationException ex)
        {
            foreach (var error in ex.Errors)
                ModelState.AddModelError(error.PropertyName, error.ErrorMessage);
            return View();
        }
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct)
    {
        await _mediator.Send(new DeactivateItemGroupCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}