using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class ResetPasswordViewModel
{
    [Required]
    [EmailAddress]
    public string Email { get; set; } = default!;
    
    [Required]
    [DataType(DataType.Password)]
    public string Password { get; set; } = default!;
    
    [DataType(DataType.Password)]
    [Display(Name = "Confirm password")]
    [Compare("Password", ErrorMessage = "Passwords do not match.")]
    public string ConfirmPassword { get; set; } = default!;
    
    public string Code { get; set; } = default!;
}
