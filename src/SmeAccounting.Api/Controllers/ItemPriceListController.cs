using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ItemPriceListController : Controller
{
    private readonly IMediator _mediator;

    public ItemPriceListController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var itemPriceLists = await _mediator.Send(new GetItemPriceListsByCompanyQuery(companyId), ct);
        return View(itemPriceLists);
    }

    [HttpGet]
    public IActionResult Create() => View();

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, long priceListId, long itemId, decimal unitPrice, string currencyCode, DateOnly effectiveFrom, DateOnly? effectiveTo, CancellationToken ct)
    {
        try
        {
            var command = new CreateItemPriceListCommand(companyId, priceListId, itemId, unitPrice, currencyCode, effectiveFrom, effectiveTo);
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
        await _mediator.Send(new DeactivateItemPriceListCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}