using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class JournalEntryController : Controller
{
    private readonly IMediator _mediator;

    public JournalEntryController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(CancellationToken ct)
    {
        var entries = await _mediator.Send(new GetFiscalPeriodsQuery(null), ct);
        var allEntries = new List<SmeAccounting.Application.DTOs.JournalEntryDto>();
        var vm = new JournalEntryViewModel(allEntries);
        return View(vm);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateJournalEntryViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateJournalEntryViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var command = new CreateJournalEntryCommand(
                model.Date, model.PeriodId, model.Description,
                null, null, model.Lines);
            await _mediator.Send(command, ct);
            return RedirectToAction(nameof(Index));
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
    public async Task<IActionResult> Post(long id, CancellationToken ct)
    {
        await _mediator.Send(new PostJournalEntryCommand(id), ct);
        return RedirectToAction(nameof(Index));
    }
}
