using FluentValidation; using MediatR; using Microsoft.AspNetCore.Mvc; using SmeAccounting.Application.Commands; using SmeAccounting.Application.Queries;
namespace SmeAccounting.Api.Controllers;
public class InventoryValuationPolicyController : Controller
{
    private readonly IMediator _mediator;
    public InventoryValuationPolicyController(IMediator mediator) => _mediator = mediator;
    [HttpGet] public async Task<IActionResult> Index(long companyId, CancellationToken ct) => View(await _mediator.Send(new GetInventoryValuationPoliciesByCompanyQuery(companyId), ct));
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Create(long companyId, string code, string name, string valuationMethod, string? description, CancellationToken ct)
    {
        try { await _mediator.Send(new CreateInventoryValuationPolicyCommand(companyId, code, name, valuationMethod, description), ct); return RedirectToAction(nameof(Index), new { companyId }); }
        catch (ValidationException ex) { foreach(var e in ex.Errors) ModelState.AddModelError(e.PropertyName, e.ErrorMessage); return View(); }
    }
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct){ await _mediator.Send(new DeactivateInventoryValuationPolicyCommand(id), ct); return RedirectToAction(nameof(Index), new { companyId });}
}
