using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class CreatePaymentMethodViewModel
{
    [Required]
    public long CompanyId { get; set; }

    [Required]
    [StringLength(20)]
    public string Code { get; set; } = string.Empty;

    [Required]
    [StringLength(200)]
    public string Name { get; set; } = string.Empty;

    [Required]
    public string Category { get; set; } = string.Empty;

    public bool RequiresBankAccount { get; set; }

    [StringLength(500)]
    public string? Description { get; set; }
}
