using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class ItemBarcode : BaseEntity
{
    public long CompanyId { get; private set; }
    public long ItemId { get; private set; }
    public string Barcode { get; private set; } = string.Empty;
    public BarcodeType BarcodeType { get; private set; }
    public long? UomId { get; private set; }
    public bool IsPrimary { get; private set; }
    public bool IsActive { get; private set; } = true;

    private ItemBarcode() { }

    public ItemBarcode(long companyId, long itemId, string barcode, BarcodeType barcodeType, long? uomId = null, bool isPrimary = false)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (itemId <= 0) throw new DomainException("ItemId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(barcode)) throw new DomainException("Barcode is required.");
        if (barcode.Length > 20) throw new DomainException("Barcode cannot exceed 20 characters.");
        if (uomId.HasValue && uomId <= 0) throw new DomainException("UomId must be greater than zero when specified.");

        CompanyId = companyId;
        ItemId = itemId;
        Barcode = barcode;
        BarcodeType = barcodeType;
        UomId = uomId;
        IsPrimary = isPrimary;

        AddDomainEvent(new ItemBarcodeCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}