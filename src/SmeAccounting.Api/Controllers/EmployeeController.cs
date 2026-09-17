using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class EmployeeController : Controller
{
    private readonly IMediator _mediator;

    public EmployeeController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var employees = await _mediator.Send(new GetEmployeesByCompanyQuery(companyId), ct);
        return View(employees);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateEmployeeViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateEmployeeViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var command = new CreateEmployeeCommand(
                model.CompanyId,
                model.Code,
                model.Name,
                model.EmployeeNumber,
                model.TaxCode,
                model.Address,
                model.Phone,
                model.Email,
                model.HireDate,
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
        await _mediator.Send(new DeactivateEmployeeCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
