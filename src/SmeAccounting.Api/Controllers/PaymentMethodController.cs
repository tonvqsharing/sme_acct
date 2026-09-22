using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Api.Controllers;

public class PaymentMethodController : Controller
{
    private readonly IMediator _mediator;

    public PaymentMethodController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var methods = await _mediator.Send(new GetPaymentMethodsByCompanyQuery(companyId), ct);
        return View(methods);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreatePaymentMethodViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreatePaymentMethodViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var category = Enum.Parse<PaymentMethodCategory>(model.Category);
            var command = new CreatePaymentMethodCommand(
                model.CompanyId,
                model.Code,
                model.Name,
                category,
                model.RequiresBankAccount,
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
        await _mediator.Send(new DeactivatePaymentMethodCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
