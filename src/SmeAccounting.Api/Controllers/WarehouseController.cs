using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class WarehouseController : Controller
{
    private readonly IMediator _mediator;
    public WarehouseController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var whs = await _mediator.Send(new GetWarehousesByCompanyQuery(companyId), ct);
        return View(whs);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, string code, string name, string? address, string? description, CancellationToken ct)
    {
        try
        {
            var cmd = new CreateWarehouseCommand(companyId, code, name, address, description);
            await _mediator.Send(cmd, ct);
            return RedirectToAction(nameof(Index), new { companyId });
        }
        catch (ValidationException ex)
        {
            foreach (var e in ex.Errors) ModelState.AddModelError(e.PropertyName, e.ErrorMessage);
            return View();
        }
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct)
    {
        await _mediator.Send(new DeactivateWarehouseCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
