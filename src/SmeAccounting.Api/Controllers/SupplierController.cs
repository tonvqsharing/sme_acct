using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class SupplierController : Controller
{
    private readonly IMediator _mediator;

    public SupplierController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var suppliers = await _mediator.Send(new GetSuppliersByCompanyQuery(companyId), ct);
        return View(suppliers);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateSupplierViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateSupplierViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var command = new CreateSupplierCommand(
                model.CompanyId,
                model.Code,
                model.Name,
                model.TaxCode,
                model.Address,
                model.Phone,
                model.Email,
                model.PaymentTermId,
                model.DefaultTaxTypeId,
                model.Description);
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
        await _mediator.Send(new DeactivateSupplierCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
