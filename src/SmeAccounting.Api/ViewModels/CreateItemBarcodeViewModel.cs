using System.ComponentModel.DataAnnotations;

namespace SmeAccounting.Api.ViewModels;

public class CreateItemBarcodeViewModel
{
    [Required]
    public long CompanyId { get; set; }

    [Required]
    public long ItemId { get; set; }

    [Required]
    [StringLength(20)]
    public string Barcode { get; set; } = string.Empty;

    [Required]
    public string BarcodeType { get; set; } = string.Empty;

    public long? UomId { get; set; }

    public bool IsPrimary { get; set; }
}