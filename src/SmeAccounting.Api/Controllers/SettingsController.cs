using Microsoft.AspNetCore.Mvc;

namespace SmeAccounting.Api.Controllers;

public class SettingsController : Controller
{
    public IActionResult Index() => View();
}
