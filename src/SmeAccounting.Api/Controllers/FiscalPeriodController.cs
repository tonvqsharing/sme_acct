using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class FiscalPeriodController : Controller
{
    private readonly IMediator _mediator;

    public FiscalPeriodController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(CancellationToken ct)
    {
        var periods = await _mediator.Send(new GetFiscalPeriodsQuery(null), ct);
        var vm = new FiscalPeriodViewModel(periods);
        return View(vm);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Open(long yearId, int month, CancellationToken ct)
    {
        await _mediator.Send(new OpenFiscalPeriodCommand(yearId, month), ct);
        return RedirectToAction(nameof(Index));
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Close(long id, CancellationToken ct)
    {
        await _mediator.Send(new CloseFiscalPeriodCommand(id), ct);
        return RedirectToAction(nameof(Index));
    }
}
