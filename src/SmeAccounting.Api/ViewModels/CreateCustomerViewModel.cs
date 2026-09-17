using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class CreateCustomerViewModel
{
    [Required]
    public long CompanyId { get; set; }

    [Required]
    [StringLength(20)]
    public string Code { get; set; } = string.Empty;

    [Required]
    [StringLength(200)]
    public string Name { get; set; } = string.Empty;

    [StringLength(20)]
    public string? TaxCode { get; set; }

    [StringLength(500)]
    public string? Address { get; set; }

    [StringLength(50)]
    public string? Phone { get; set; }

    [StringLength(200)]
    public string? Email { get; set; }

    [StringLength(500)]
    public string? Description { get; set; }
}
