using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using SmeAccounting.Api.ViewModels;
using SmeAccounting.Infrastructure.Identity;

namespace SmeAccounting.Api.Controllers;

public class AccountsController : Controller
{
    private readonly SignInManager<ApplicationUser> _signInManager;
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly ILogger<AccountsController> _logger;
    
    public AccountsController(
        SignInManager<ApplicationUser> signInManager,
        UserManager<ApplicationUser> userManager,
        ILogger<AccountsController> logger)
    {
        _signInManager = signInManager;
        _userManager = userManager;
        _logger = logger;
    }
    
    [HttpGet]
    public IActionResult Login(string? returnUrl = null)
    {
        ViewData["ReturnUrl"] = returnUrl;
        return View();
    }
    
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Login(LoginViewModel model, string? returnUrl = null)
    {
        ViewData["ReturnUrl"] = returnUrl;
        
        if (!ModelState.IsValid)
            return View(model);
        
        var user = await _userManager.FindByEmailAsync(model.Email);
        if (user == null || !user.IsEnabled)
        {
            ModelState.AddModelError(string.Empty, "Invalid login attempt.");
            return View(model);
        }
        
        var result = await _signInManager.PasswordSignInAsync(
            user, model.Password, model.RememberMe, lockoutOnFailure: true);
        
        if (result.Succeeded)
        {
            user.LastLoginAtUtc = DateTime.UtcNow;
            await _userManager.UpdateAsync(user);
            
            _logger.LogInformation("User {Email} logged in", model.Email);
            return LocalRedirect(returnUrl ?? "/");
        }
        
        if (result.IsLockedOut)
        {
            _logger.LogWarning("User {Email} locked out", model.Email);
            ModelState.AddModelError(string.Empty, "Account locked out.");
            return View(model);
        }
        
        ModelState.AddModelError(string.Empty, "Invalid login attempt.");
        return View(model);
    }
    
    [HttpPost]
    [ValidateAntiForgeryToken]
    [Authorize]
    public async Task<IActionResult> Logout()
    {
        await _signInManager.SignOutAsync();
        _logger.LogInformation("User logged out");
        return RedirectToAction("Login");
    }
    
    [HttpGet]
    public IActionResult AccessDenied()
    {
        return View();
    }
    
    [HttpGet]
    public IActionResult ForgotPassword() => View();
    
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> ForgotPassword(ForgotPasswordViewModel model)
    {
        if (!ModelState.IsValid) return View(model);
        
        var user = await _userManager.FindByEmailAsync(model.Email);
        if (user != null)
        {
            var token = await _userManager.GeneratePasswordResetTokenAsync(user);
            _logger.LogInformation("Password reset token generated for {Email}", model.Email);
            // TODO: Send email with reset link
        }
        
        return RedirectToAction("ForgotPasswordConfirmation");
    }
    
    [HttpGet]
    public IActionResult ForgotPasswordConfirmation() => View();
    
    [HttpGet]
    public IActionResult ResetPassword(string? code = null, string? email = null)
    {
        if (code == null || email == null)
            return BadRequest("A code and email must be supplied for password reset.");
        
        return View(new ResetPasswordViewModel { Code = code, Email = email });
    }
    
    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> ResetPassword(ResetPasswordViewModel model)
    {
        if (!ModelState.IsValid) return View(model);
        
        var user = await _userManager.FindByEmailAsync(model.Email);
        if (user == null)
        {
            return RedirectToAction("ResetPasswordConfirmation");
        }
        
        var result = await _userManager.ResetPasswordAsync(user, model.Code, model.Password);
        if (result.Succeeded)
        {
            _logger.LogInformation("Password reset for {Email}", model.Email);
            return RedirectToAction("ResetPasswordConfirmation");
        }
        
        foreach (var error in result.Errors)
        {
            ModelState.AddModelError(string.Empty, error.Description);
        }
        
        return View(model);
    }
    
    [HttpGet]
    public IActionResult ResetPasswordConfirmation() => View();
}
