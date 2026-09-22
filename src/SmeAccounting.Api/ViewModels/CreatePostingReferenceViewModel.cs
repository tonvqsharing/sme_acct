using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class CreatePostingReferenceViewModel
{
    [Required]
    public long CompanyId { get; set; }

    [Required]
    public long JournalEntryId { get; set; }

    [Required]
    [StringLength(100)]
    public string SourceType { get; set; } = string.Empty;

    [Required]
    public long SourceId { get; set; }
}
