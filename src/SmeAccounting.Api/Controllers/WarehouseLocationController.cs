using Microsoft.AspNetCore.Mvc;
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.Queries;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Api.Controllers;

[Route("WarehouseLocation")]
public sealed class WarehouseLocationController : Controller
{
    private readonly IMediator _mediator;

    public WarehouseLocationController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet("Index")]
    public async Task<IActionResult> Index(long companyId)
    {
        var items = await _mediator.Send(new GetWarehouseLocationsByCompanyQuery(companyId));
        return View(items);
    }

    [HttpGet("Create")]
    public IActionResult Create()
    {
        return View();
    }

    [HttpPost("Create")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(
        long companyId,
        long warehouseId,
        string code,
        string name,
        string? description = null)
    {
        try
        {
            await _mediator.Send(new CreateWarehouseLocationCommand(companyId, warehouseId, code, name, description));
            return RedirectToAction(nameof(Index), new { companyId });
        }
        catch (FluentValidation.ValidationException ex)
        {
            foreach (var error in ex.Errors)
                ModelState.AddModelError(error.PropertyName, error.ErrorMessage);
            return View();
        }
    }

    [HttpPost("Deactivate")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Deactivate(long id, long companyId)
    {
        await _mediator.Send(new DeactivateWarehouseLocationCommand(id));
        return RedirectToAction(nameof(Index), new { companyId });
    }
}