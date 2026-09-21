using FluentValidation; using MediatR; using Microsoft.AspNetCore.Mvc; using SmeAccounting.Application.Commands; using SmeAccounting.Application.Queries;
namespace SmeAccounting.Api.Controllers;
public class ItemController : Controller
{
    private readonly IMediator _mediator;
    public ItemController(IMediator mediator) => _mediator = mediator;
    [HttpGet] public async Task<IActionResult> Index(long companyId, CancellationToken ct) => View(await _mediator.Send(new GetItemsByCompanyQuery(companyId), ct));
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Create(long companyId, string code, string name, bool isStockItem, bool isServiceItem, long? itemCategoryId, long? uomId, string? description, CancellationToken ct)
    {
        try { await _mediator.Send(new CreateItemCommand(companyId, code, name, isStockItem, isServiceItem, itemCategoryId, uomId, description), ct); return RedirectToAction(nameof(Index), new { companyId }); }
        catch (ValidationException ex) { foreach(var e in ex.Errors) ModelState.AddModelError(e.PropertyName, e.ErrorMessage); return View(); }
    }
    [HttpPost][ValidateAntiForgeryToken] public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct){ await _mediator.Send(new DeactivateItemCommand(id), ct); return RedirectToAction(nameof(Index), new { companyId });}
}
