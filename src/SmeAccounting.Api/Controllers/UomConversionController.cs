using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class UomConversionController : Controller
{
    private readonly IMediator _mediator;
    public UomConversionController(IMediator mediator) => _mediator = mediator;

    [HttpGet]
    public async Task<IActionResult> Index(long companyId, CancellationToken ct)
    {
        var convs = await _mediator.Send(new GetUomConversionsByCompanyQuery(companyId), ct);
        return View(convs);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(long companyId, long fromUomId, long toUomId, decimal factor, CancellationToken ct)
    {
        try
        {
            var cmd = new CreateUomConversionCommand(companyId, fromUomId, toUomId, factor);
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
        await _mediator.Send(new DeactivateUomConversionCommand(id), ct);
        return RedirectToAction(nameof(Index), new { companyId });
    }
}
