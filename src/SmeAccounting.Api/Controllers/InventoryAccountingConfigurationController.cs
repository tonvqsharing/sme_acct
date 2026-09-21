using FluentValidation; using MediatR; using Microsoft.AspNetCore.Mvc; using SmeAccounting.Application.Commands; using SmeAccounting.Application.Queries;
namespace SmeAccounting.Api.Controllers;
public class InventoryAccountingConfigurationController : Controller
{
    private readonly IMediator _mediator;
    public InventoryAccountingConfigurationController(IMediator mediator) => _mediator = mediator;
    [HttpGet] public async Task<IActionResult> Index(long companyId, CancellationToken ct) => View(await _mediator.Send(new GetInventoryAccountingConfigurationByCompanyQuery(companyId), ct));
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Create(long companyId, long inventoryAccountId, long cogsAccountId, long? gainAccountId, long? lossAccountId, CancellationToken ct)
    {
        try { await _mediator.Send(new CreateInventoryAccountingConfigurationCommand(companyId, inventoryAccountId, cogsAccountId, gainAccountId, lossAccountId), ct); return RedirectToAction(nameof(Index), new { companyId }); }
        catch (ValidationException ex) { foreach(var e in ex.Errors) ModelState.AddModelError(e.PropertyName, e.ErrorMessage); return View(); }
    }
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct){ await _mediator.Send(new DeactivateInventoryAccountingConfigurationCommand(id), ct); return RedirectToAction(nameof(Index), new { companyId });}
}
