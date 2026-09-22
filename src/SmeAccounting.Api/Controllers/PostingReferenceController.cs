using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class PostingReferenceController : Controller
{
    private readonly IMediator _mediator;

    public PostingReferenceController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Details(long id, CancellationToken ct)
    {
        var dto = await _mediator.Send(new GetPostingReferenceByIdQuery(id), ct);
        return View(dto);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreatePostingReferenceViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreatePostingReferenceViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var command = new CreatePostingReferenceCommand(
                model.CompanyId,
                model.JournalEntryId,
                model.SourceType,
                model.SourceId);
            var result = await _mediator.Send(command, ct);
            return RedirectToAction(nameof(Details), new { id = result.Id });
        }
        catch (ValidationException ex)
        {
            foreach (var error in ex.Errors)
                ModelState.AddModelError(error.PropertyName, error.ErrorMessage);
            return View(model);
        }
    }
}
