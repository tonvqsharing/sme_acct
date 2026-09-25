using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ItemReorderLevelController : Controller
{
    private readonly IMediator _mediator;
    public ItemReorderLevelController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
        => View(await _mediator.Send(new GetItemReorderLevelsByCompanyQuery(companyId), ct));

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, long itemId, decimal minimumQuantity, long? warehouseId, decimal? maximumQuantity, CancellationToken ct)
    {
        try
        {
            await _mediator.Send(new CreateItemReorderLevelCommand(companyId, itemId, minimumQuantity, warehouseId, maximumQuantity), ct);
            return RedirectToAction(nameof(Index), new { companyId });
        }
        catch (ValidationException ex)
        {
            foreach (var e in ex.Errors)
                ModelState.AddModelError(e.PropertyName, e.ErrorMessage);
            return View();
        }
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct)
    {
        await _mediator.Send(new DeactivateItemReorderLevelCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
