using System.ComponentModel.DataAnnotations;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Api.ViewModels;

public class CreateJournalEntryViewModel
{
    [Required]
    [Display(Name = "Mã công ty")]
    public long CompanyId { get; set; }

    [Required(ErrorMessage = "Ngày hạch toán là bắt buộc")]
    [DataType(DataType.Date)]
    [Display(Name = "Ngày hạch toán")]
    public DateTimeOffset Date { get; set; } = DateTimeOffset.UtcNow;

    [Required(ErrorMessage = "Kỳ kế toán là bắt buộc")]
    [Display(Name = "Kỳ kế toán")]
    public long PeriodId { get; set; }

    [StringLength(500)]
    [Display(Name = "Diễn giải")]
    public string? Description { get; set; }

    public List<JournalEntryLineInput> Lines { get; set; } = [];
}
