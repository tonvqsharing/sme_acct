using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class CustomerController : Controller
{
    private readonly IMediator _mediator;

    public CustomerController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var customers = await _mediator.Send(new GetCustomersByCompanyQuery(companyId), ct);
        return View(customers);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateCustomerViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateCustomerViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var command = new CreateCustomerCommand(
                model.CompanyId,
                model.Code,
                model.Name,
                model.TaxCode,
                model.Address,
                model.Phone,
                model.Email,
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
        await _mediator.Send(new DeactivateCustomerCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
