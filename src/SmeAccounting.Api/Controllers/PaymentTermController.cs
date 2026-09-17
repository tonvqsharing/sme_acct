using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Api.Controllers;

public class PaymentTermController : Controller
{
    private readonly IMediator _mediator;

    public PaymentTermController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var terms = await _mediator.Send(new GetPaymentTermsByCompanyQuery(companyId), ct);
        return View(terms);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreatePaymentTermViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreatePaymentTermViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var paymentTermType = Enum.Parse<PaymentTermType>(model.PaymentTermType);
            var command = new CreatePaymentTermCommand(
                model.CompanyId,
                model.Code,
                model.Name,
                paymentTermType,
                model.Days,
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
        await _mediator.Send(new DeactivatePaymentTermCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
