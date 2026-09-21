using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ItemCategoryController : Controller
{
    private readonly IMediator _mediator;
    public ItemCategoryController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var cats = await _mediator.Send(new GetItemCategoriesByCompanyQuery(companyId), ct);
        return View(cats);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, string code, string name, long? parentId, string? description, CancellationToken ct)
    {
        try
        {
            var cmd = new CreateItemCategoryCommand(companyId, code, name, parentId, description);
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
        await _mediator.Send(new DeactivateItemCategoryCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
