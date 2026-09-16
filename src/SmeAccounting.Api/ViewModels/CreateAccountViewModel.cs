using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class CreateAccountViewModel
{
    [Required(ErrorMessage = "Mã tài khoản là bắt buộc")]
    [RegularExpression(@"^\d{4,}$", ErrorMessage = "Phải là số, ít nhất 4 chữ số")]
    [Display(Name = "Mã tài khoản")]
    public string Code { get; set; } = string.Empty;

    [Required(ErrorMessage = "Tên tài khoản là bắt buộc")]
    [StringLength(200, MinimumLength = 2)]
    [Display(Name = "Tên tài khoản")]
    public string Name { get; set; } = string.Empty;

    [Required(ErrorMessage = "Loại tài khoản là bắt buộc")]
    [Display(Name = "Loại tài khoản")]
    public string AccountType { get; set; } = string.Empty;

    [Required(ErrorMessage = "CompanyId là bắt buộc")]
    [Display(Name = "CompanyId")]
    public long CompanyId { get; set; }

    [Required(ErrorMessage = "Số dư bình thường là bắt buộc")]
    [Display(Name = "Số dư bình thường")]
    public string NormalBalance { get; set; } = string.Empty;

    [Display(Name = "Tài khoản cha")]
    public long? ParentId { get; set; }

    [Display(Name = "Nhóm tài khoản")]
    public long? AccountGroupId { get; set; }

    [Display(Name = "Mô tả")]
    public string? Description { get; set; }
}
