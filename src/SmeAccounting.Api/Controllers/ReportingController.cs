using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ReportingController : Controller
{
    private readonly IMediator _mediator;

    public ReportingController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> BalanceSheet(long? periodId, CancellationToken ct)
    {
        var id = periodId ?? 1;
        var report = await _mediator.Send(new GetBalanceSheetQuery(id), ct);
        return View(report);
    }

    [HttpGet]
    public async Task<IActionResult> IncomeStatement(long? periodId, CancellationToken ct)
    {
        var id = periodId ?? 1;
        var report = await _mediator.Send(new GetIncomeStatementQuery(id), ct);
        return View(report);
    }
}
