using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class ForgotPasswordViewModel
{
    [Required]
    [EmailAddress]
    public string Email { get; set; } = default!;
}
