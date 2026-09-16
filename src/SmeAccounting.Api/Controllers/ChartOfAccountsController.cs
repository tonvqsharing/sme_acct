using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;

namespace SmeAccounting.Api.Controllers;

public class ChartOfAccountsController : Controller
{
    private readonly IMediator _mediator;

    public ChartOfAccountsController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<IActionResult> Index(CancellationToken ct)
    {
        var accounts = await _mediator.Send(new GetAccountsByGroupQuery(0), ct);
        var vm = new ChartOfAccountsViewModel(accounts, null);
        return View(vm);
    }

    [HttpGet]
    public IActionResult Create() => View(new CreateAccountViewModel());

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(CreateAccountViewModel model, CancellationToken ct)
    {
        if (!ModelState.IsValid) return View(model);

        try
        {
            var accountType = Enum.Parse<SmeAccounting.Domain.ValueObjects.AccountType>(model.AccountType);
            var command = new CreateAccountCommand(
                model.Code, model.Name, accountType, model.ParentId, model.AccountGroupId);
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
    public async Task<IActionResult> Deprecate(long id, CancellationToken ct)
    {
        await _mediator.Send(new DeprecateAccountCommand(id), ct);
        return RedirectToAction(nameof(Index));
    }
}
