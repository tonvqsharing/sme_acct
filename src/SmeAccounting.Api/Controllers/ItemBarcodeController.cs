using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Api.Controllers;

public class ItemBarcodeController : Controller
{
    private readonly IMediator _mediator;

    public ItemBarcodeController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var itemBarcodes = await _mediator.Send(new GetItemBarcodesByCompanyQuery(companyId), ct);
        return View(itemBarcodes);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateItemBarcodeViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateItemBarcodeViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var barcodeType = Enum.Parse<BarcodeType>(model.BarcodeType);
            var command = new CreateItemBarcodeCommand(
                model.CompanyId,
                model.ItemId,
                model.Barcode,
                barcodeType,
                model.UomId,
                model.IsPrimary);
            await _mediator.Send(command, ct);
            return RedirectToAction(nameof(Index), new { companyId = model.CompanyId });
        }
        catch (ValidationException ex)
        {
            foreach (var error in ex.Errors)
                ModelState.AddModelError(error.PropertyName, error.ErrorMessage);
            return View(model);
        }
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(long id, long companyId, CancellationToken ct)
    {
        await _mediator.Send(new DeactivateItemBarcodeCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}