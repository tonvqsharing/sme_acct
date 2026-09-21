using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class Item : BaseEntity
{
    public long CompanyId { get; private set; }
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public long? ItemCategoryId { get; private set; }
    public long? UomId { get; private set; }
    public bool IsStockItem { get; private set; }
    public bool IsServiceItem { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private Item() { }

    public Item(long companyId, string code, string name, bool isStockItem, bool isServiceItem, long? itemCategoryId = null, long? uomId = null, string? description = null)
    {
        if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code)) throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name)) throw new DomainException("Name is required.");
        if (!isStockItem && !isServiceItem) throw new DomainException("Item must be either stock or service.");
        if (isStockItem && !uomId.HasValue) throw new DomainException("UomId required for stock item.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        IsStockItem = isStockItem;
        IsServiceItem = isServiceItem;
        ItemCategoryId = itemCategoryId;
        UomId = uomId;
        Description = description;

        AddDomainEvent(new ItemCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate() => IsActive = false;
}
